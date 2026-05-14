"""
MuJoCo vision deployment: gamepad velocity commands + depth policy.
Standalone package under Humanoid_vision_mujoco (no legged_gym).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, Tuple

_DEPLOY = Path(__file__).resolve().parent
if str(_DEPLOY) not in sys.path:
    sys.path.insert(0, str(_DEPLOY))

import cv2
import mujoco
import mujoco.viewer
import numpy as np
import torch
import yaml

from vision_deploy.paths import expand_config_paths, resolve_config_path
from vision_deploy.policy_inference import VisionPolicyRunner
from utils.gamepad_utils import init_gamepad, joystick, update_cmd_from_gamepad
from utils.math_utils import get_gravity_orientation, pd_control
import utils.viewer_utils as viewer_utils
from vision_deploy.vision_depth import update_depth_cam


def _load_config(path_arg: str) -> Dict[str, Any]:
    cfg_path = resolve_config_path(path_arg)
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)
    expand_config_paths(cfg)
    return cfg


def _pelvis_body_id(m: mujoco.MjModel) -> int:
    for name in ("pelvis_link", "base_link"):
        try:
            bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, name)
            if bid >= 0:
                return bid
        except Exception:
            continue
    print("警告: 未找到 pelvis_link/base_link，使用 body 0")
    return 0


def _depth_cam_id(m: mujoco.MjModel) -> int | None:
    try:
        cid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_CAMERA, "depth_cam")
        print(f"depth_cam id = {cid}")
        return cid
    except Exception:
        print("警告: XML 中未找到相机 depth_cam")
        return None


def _build_obs(
    obs: np.ndarray,
    d: mujoco.MjData,
    default_angles: np.ndarray,
    dof_pos_scale: float,
    dof_vel_scale: float,
    ang_vel_scale: float,
    cmd: np.ndarray,
    cmd_scale: np.ndarray,
    action: np.ndarray,
    num_actions: int,
) -> None:
    qj = d.qpos[7:]
    dqj = d.qvel[6:]
    quat = d.qpos[3:7]
    omega = d.qvel[3:6]
    qj = (qj - default_angles) * dof_pos_scale
    dqj = dqj * dof_vel_scale
    gravity_orientation = get_gravity_orientation(quat)
    omega = omega * ang_vel_scale
    idx = 0
    obs[idx : idx + 3] = omega
    idx += 3
    obs[idx : idx + 3] = gravity_orientation
    idx += 3
    obs[idx : idx + 3] = cmd * cmd_scale
    idx += 3
    obs[idx : idx + num_actions] = qj
    idx += num_actions
    obs[idx : idx + num_actions] = dqj
    idx += num_actions
    obs[idx : idx + num_actions] = action


def main() -> None:
    parser = argparse.ArgumentParser(description="Vision MuJoCo deploy")
    parser.add_argument(
        "config",
        type=str,
        help="YAML in deploy_mujoco/configs/ (e.g. e3_21dof_vision.yaml) or absolute path",
    )
    args = parser.parse_args()
    config = _load_config(args.config)

    policy_path = config["policy_path"]
    xml_path = config["xml_path"]
    simulation_duration = float(config["simulation_duration"])
    simulation_dt = float(config["simulation_dt"])
    control_decimation = int(config["control_decimation"])

    kps = np.array(config["kps"], dtype=np.float32)
    kds = np.array(config["kds"], dtype=np.float32)
    default_angles = np.array(config["default_angles"], dtype=np.float32)

    ang_vel_scale = float(config["ang_vel_scale"])
    dof_pos_scale = float(config["dof_pos_scale"])
    dof_vel_scale = float(config["dof_vel_scale"])
    action_scale = float(config["action_scale"])
    cmd_scale = np.array(config["cmd_scale"], dtype=np.float32)

    num_actions = int(config["num_actions"])
    num_obs = int(config["num_obs"])
    cmd = np.array(config["cmd_init"], dtype=np.float32)

    depth_size: Tuple[int, int] = (int(config["depth_size"][0]), int(config["depth_size"][1]))
    depth_render_size = config.get("depth_render_size", [480, 640])
    depth_render_size = (int(depth_render_size[0]), int(depth_render_size[1]))
    depth_vis_rotate_k = int(config.get("depth_vis_rotate_k", 1))
    depth_buffer_use_length = int(config["depth_buffer_use_length"])
    depth_decimation = int(config["depth_decimation"])
    depth_min_range = float(config["depth_min_range"])
    depth_max_range = float(config["depth_max_range"])
    depth_noise_amp = float(config["depth_noise_amp"])

    action = np.zeros(num_actions, dtype=np.float32)
    target_dof_pos = default_angles.copy()
    obs = np.zeros(num_obs, dtype=np.float32)
    depth_hw = depth_size[0] * depth_size[1]
    depth_image_buffer = torch.zeros(
        1, depth_buffer_use_length, depth_hw, dtype=torch.float32
    )
    current_depth_img = torch.zeros(
        1, depth_buffer_use_length * depth_hw, dtype=torch.float32
    )

    counter = 0
    cam_update_counter = 0

    m = mujoco.MjModel.from_xml_path(xml_path)
    d = mujoco.MjData(m)
    m.opt.timestep = simulation_dt
    initial_qpos = d.qpos.copy()
    initial_qvel = d.qvel.copy()
    initial_cmd = cmd.copy()

    depth_cam_id = _depth_cam_id(m)
    depth_renderer = mujoco.Renderer(
        m, width=depth_render_size[1], height=depth_render_size[0]
    )
    depth_renderer.enable_depth_rendering()

    policy = VisionPolicyRunner(policy_path)

    init_gamepad(config)
    pelvis_body_id = _pelvis_body_id(m)

    last_pad_t = time.time()
    pad_interval = 0.02

    with mujoco.viewer.launch_passive(m, d) as viewer:
        t0 = time.time()
        while viewer.is_running() and time.time() - t0 < simulation_duration:
            step_start = time.time()

            if viewer_utils.reset_requested:
                d.qpos[:] = initial_qpos
                d.qvel[:] = initial_qvel
                cmd[:] = initial_cmd
                action[:] = 0.0
                target_dof_pos[:] = default_angles.copy()
                counter = 0
                cam_update_counter = 0
                d.xfrc_applied[:] = 0.0
                depth_image_buffer.zero_()
                current_depth_img = torch.zeros(
                    1, depth_buffer_use_length * depth_hw, dtype=torch.float32
                )
                policy.reset()
                viewer_utils.reset_requested = False
                print("已重置")
                mujoco.mj_step(m, d)
                viewer.sync()
                continue

            now = time.time()
            if now - last_pad_t >= pad_interval:
                cmd = update_cmd_from_gamepad(cmd)
                last_pad_t = now

            tau = pd_control(
                target_dof_pos, d.qpos[7:], kps, np.zeros_like(kds), d.qvel[6:], kds
            )
            d.ctrl[:] = tau
            mujoco.mj_step(m, d)
            counter += 1

            if counter % control_decimation == 0:
                _build_obs(
                    obs,
                    d,
                    default_angles,
                    dof_pos_scale,
                    dof_vel_scale,
                    ang_vel_scale,
                    cmd,
                    cmd_scale,
                    action,
                    num_actions,
                )
                if depth_cam_id is not None:
                    depth_img, depth_raw = update_depth_cam(
                        depth_renderer,
                        d,
                        depth_cam_id,
                        depth_size,
                        depth_min_range,
                        depth_max_range,
                        depth_noise_amp,
                        cam_update_counter,
                        depth_decimation,
                        depth_vis_rotate_k=depth_vis_rotate_k,
                    )
                    if depth_img is not None:
                        if (depth_image_buffer == 0).all():
                            depth_image_buffer = depth_img.unsqueeze(1).repeat(
                                1, depth_buffer_use_length, 1
                            )
                        else:
                            depth_image_buffer = torch.cat(
                                [depth_image_buffer[:, 1:, :], depth_img.unsqueeze(1)],
                                dim=1,
                            )
                        current_depth_img = depth_image_buffer.reshape(1, -1)
                        if depth_raw is not None:
                            disp = np.clip(depth_raw, depth_min_range, depth_max_range)
                            disp = (disp - depth_min_range) / (
                                depth_max_range - depth_min_range
                            )
                            if disp.shape != (depth_render_size[0], depth_render_size[1]):
                                disp = cv2.resize(
                                    disp,
                                    (depth_render_size[1], depth_render_size[0]),
                                    interpolation=cv2.INTER_NEAREST,
                                )
                            cv2.namedWindow("depth (raw)", cv2.WINDOW_NORMAL)
                            cv2.imshow("depth (raw)", disp)
                            cv2.waitKey(1)
                    elif (depth_image_buffer != 0).any():
                        current_depth_img = depth_image_buffer.reshape(1, -1)
                    else:
                        current_depth_img = torch.zeros(
                            1, depth_buffer_use_length * depth_hw, dtype=torch.float32
                        )
                else:
                    current_depth_img = torch.zeros(
                        1, depth_buffer_use_length * depth_hw, dtype=torch.float32
                    )

                cam_update_counter += 1
                obs_t = torch.from_numpy(obs).unsqueeze(0).float()
                action = policy.infer(obs_t, current_depth_img)
                target_dof_pos = action * action_scale + default_angles

            viewer_utils.update_viewer_settings(viewer, pelvis_body_id, d)
            viewer.sync()
            dt_rem = m.opt.timestep - (time.time() - step_start)
            if dt_rem > 0:
                time.sleep(dt_rem)

    if joystick is not None:
        joystick.quit()
    try:
        import pygame

        pygame.quit()
    except Exception:
        pass


if __name__ == "__main__":
    main()

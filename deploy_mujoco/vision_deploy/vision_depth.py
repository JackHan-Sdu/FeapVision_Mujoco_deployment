"""Depth camera capture and preprocessing for vision policy (MuJoCo)."""
from __future__ import annotations

from typing import Optional, Tuple

import cv2
import mujoco
import numpy as np
import torch


def normalize_depth_image(
    depth_image: np.ndarray, min_range: float, max_range: float
) -> np.ndarray:
    depth_image = np.clip(depth_image, min_range, max_range)
    depth_image = (depth_image - min_range) / (max_range - min_range) - 0.5
    return depth_image


def update_depth_cam(
    depth_renderer: mujoco.Renderer,
    d: mujoco.MjData,
    depth_cam_id: int,
    depth_size: Tuple[int, int],
    depth_min_range: float,
    depth_max_range: float,
    depth_noise_amp: float,
    counter: int,
    depth_decimation: int,
    depth_vis_rotate_k: int = 1,
) -> Tuple[Optional[torch.Tensor], Optional[np.ndarray]]:
    """
    Returns:
        (normalized_depth [1, H*W] tensor or None if skipped frame, raw depth for vis [H,W] or None)
    """
    if counter % depth_decimation != 0:
        return None, None

    depth_renderer.update_scene(d, camera=depth_cam_id)
    depth_image_raw_full = depth_renderer.render()
    depth_image_raw_for_vis = (
        np.rot90(depth_image_raw_full, k=depth_vis_rotate_k)
        if depth_vis_rotate_k != 0
        else depth_image_raw_full.copy()
    )

    depth_image_processed = np.rot90(depth_image_raw_full, k=1)
    depth_image_processed = cv2.resize(
        depth_image_processed,
        (depth_size[1], depth_size[0]),
        interpolation=cv2.INTER_AREA,
    )

    if depth_noise_amp > 0:
        depth_image_processed += depth_noise_amp * np.random.randn(
            *depth_image_processed.shape
        )

    depth_image_normalized = normalize_depth_image(
        depth_image_processed, depth_min_range, depth_max_range
    )
    depth_image_tensor = torch.tensor(depth_image_normalized, dtype=torch.float32).reshape(
        1, -1
    )
    return depth_image_tensor, depth_image_raw_for_vis

# MuJoCo 人形视觉跑酷部署

在 MuJoCo 中运行**本体观测 + 深度图 + 手柄速度指令**的 TorchScript 策略。本目录独立于 `legged_gym`，核心逻辑在 `vision_deploy/`。

## 环境（Conda）

```bash
conda create -n humanoid_mujoco python=3.10 -y
conda activate humanoid_mujoco
```

安装依赖（与脚本 import 一致）：

```bash
pip install mujoco numpy torch opencv-python pyyaml pygame
```

可选：若需 GPU 版 PyTorch，请按 [PyTorch 官网](https://pytorch.org/) 选择对应 CUDA 版本的安装命令，再单独安装其余包。

## 依赖说明

| 包 | 用途 |
|----|------|
| `mujoco` | 仿真与渲染 |
| `numpy` | 数值计算 |
| `torch` | 加载并推理 `*.pt`（TorchScript） |
| `opencv-python` | 深度图可视化窗口 |
| `pyyaml` | 读取 `configs/*.yaml` |
| `pygame` | 手柄输入 |

## 手柄（北通 / 罗技）

在配置 YAML 中设置 `gamepad_type`：

- **罗技**：`gamepad_type: logitech`（默认轴映射 `[0,1,2,3]`）
- **北通**：`gamepad_type: betop`（轴映射 `[0,1,3,4]`）

程序会尝试加载 `vision_deploy/gamepad_calibration_<类型>.json`；若无校准文件仍可使用默认映射。需要精确映射时可运行：

```bash
cd /path/to/Humanoid_vision_mujoco/deploy_mujoco
python vision_deploy/calibrate_gamepad.py
```

生成 JSON 后保持 `gamepad_type` 与文件名一致，或通过配置项 `gamepad_calibration_file` 指定路径（见 `utils/gamepad_utils.py`）。

## 使用

1. 将导出的策略放到 `policy/`，例如 `policy/motion_lstm.pt`，与 YAML 中 `policy_path` 一致（可用占位符 `{DEPLOY_DIR}`）。
2. 确认场景 XML 含名为 **`depth_cam`** 的相机（默认见 `{PACKAGE_ROOT}/resources/robots/e3_21dof/scene_terrain.xml`）。
3. 启动（任意工作目录均可，脚本会将 `deploy_mujoco` 加入 `sys.path`）：

```bash
python /path/to/Humanoid_vision_mujoco/deploy_mujoco/deploy_mujoco_vision.py e3_vision.yaml
```

或：

```bash
cd /path/to/Humanoid_vision_mujoco/deploy_mujoco
python deploy_mujoco_vision.py configs/e3_vision.yaml
```

## 目录速览

| 路径 | 说明 |
|------|------|
| `deploy_mujoco_vision.py` | 入口 |
| `vision_deploy/paths.py` | `{DEPLOY_DIR}`、`{PACKAGE_ROOT}` 占位符展开 |
| `vision_deploy/policy_inference.py` | TorchScript 策略封装 |
| `vision_deploy/vision_depth.py` | 深度预处理 |
| `configs/*.yaml` | 仿真、PD、深度、策略路径等 |
| `policy/` | 放置 `motion_lstm.pt` |
| `utils/` | PD、重力方向、手柄、Viewer 辅助 |

路径占位：`PACKAGE_ROOT` → 仓库根 `Humanoid_vision_mujoco`；`DEPLOY_DIR` → 本目录 `deploy_mujoco`。

## 模块引用

已将 `deploy_mujoco` 加入 `sys.path` 后：

```python
from vision_deploy import DEPLOY_DIR, VisionPolicyRunner, resolve_config_path
```

Viewer 与手柄快捷键以 `utils/gamepad_utils.py`、`utils/viewer_utils.py` 为准。

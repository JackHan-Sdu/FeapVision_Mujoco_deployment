# MuJoCo 人形视觉跑酷部署

<p align="center">
  <b>本体观测 + 深度图 + 手柄速度指令 的 TorchScript 人形机器人部署框架</b>
</p>

<p align="center">
  <a href="https://www.bilibili.com/video/BV1Bo5s63Ed2/">
    <img src="https://img.shields.io/badge/Bilibili-Demo-%23FB7299?style=for-the-badge&logo=bilibili">
  </a>
  <img src="https://img.shields.io/badge/python-3.10-blue?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/MuJoCo-3.x-orange?style=for-the-badge">
  <img src="https://img.shields.io/badge/TorchScript-Inference-red?style=for-the-badge">
  <img src="https://img.shields.io/badge/platform-linux-black?style=for-the-badge&logo=linux">
</p>

---

## Demo 视频
<p align="center">
  <a href="https://www.bilibili.com/video/BV1Bo5s63Ed2/">
    <img src="https://img.shields.io/badge/Bilibili-Demo-%23FB7299?style=for-the-badge&logo=bilibili&logoColor=white">
  </a>
</p>

<p align="center">
  <a href="https://www.bilibili.com/video/BV1Bo5s63Ed2/">
    <img src="docs/demo.gif" width="90%">
  </a>
</p>

<p align="center">
🎥 点击图片跳转 Bilibili Demo 视频
</p>

---

在 MuJoCo 中运行 **本体观测 + 深度图 + 手柄速度指令** 的 TorchScript 策略。

本目录具备

- 人形机器人实时运动控制
- 深度视觉观测
- 手柄速度控制
- TorchScript 推理部署
- 地形运动
- MuJoCo Viewer 可视化

---

# 环境（Conda）

```bash
conda create -n humanoid_mujoco python=3.10 -y
conda activate humanoid_mujoco
```

安装依赖（与脚本 import 一致）：

```bash
pip install mujoco numpy torch opencv-python pyyaml pygame
```

可选：若需 GPU 版 PyTorch，请按：

https://pytorch.org/

选择对应 CUDA 版本安装命令，再单独安装其余包。

---

# 依赖说明

| 包 | 用途 |
|----|------|
| `mujoco` | 仿真与渲染 |
| `numpy` | 数值计算 |
| `torch` | 加载并推理 `*.pt`（TorchScript） |
| `opencv-python` | 深度图可视化窗口 |
| `pyyaml` | 读取 `configs/*.yaml` |
| `pygame` | 手柄输入 |

---

# 系统结构

```text
Depth Camera
      ↓
Depth Processing
      ↓
Observation Builder
      ↓
TorchScript Policy
      ↓
PD Controller
      ↓
MuJoCo Humanoid
```

---

# 手柄（北通 / 罗技）

在配置 YAML 中设置：

```yaml
gamepad_type: logitech
```

或：

```yaml
gamepad_type: betop
```

默认轴映射：

| 手柄 | 轴映射 |
|---|---|
| 罗技 | `[0,1,2,3]` |
| 北通 | `[0,1,3,4]` |

程序会尝试加载：

```text
vision_deploy/gamepad_calibration_<类型>.json
```

若无校准文件仍可使用默认映射。

---

# 手柄校准

需要精确映射时运行：

```bash
cd /path/to/Humanoid_vision_mujoco/deploy_mujoco
python vision_deploy/calibrate_gamepad.py
```

生成 JSON 后：

- 保持 `gamepad_type` 与文件名一致
- 或通过 `gamepad_calibration_file` 指定路径

具体见：

```text
utils/gamepad_utils.py
```

---

# 使用

## 1. 放置 TorchScript 策略

将导出的策略放到：

```text
policy/
```

例如：

```text
policy/motion_lstm.pt
```

并与 YAML 中：

```yaml
policy_path:
```

保持一致。

支持占位符：

```text
{DEPLOY_DIR}
```

---

## 2. 检查深度相机

确认场景 XML 含名为：

```text
depth_cam
```

的相机。

默认场景：

```text
{PACKAGE_ROOT}/resources/robots/e3_21dof/scene_terrain.xml
```

---

## 3. 启动部署

任意工作目录均可，脚本会自动将：

```text
deploy_mujoco
```

加入 `sys.path`。

启动：

```bash
python /path/to/Humanoid_vision_mujoco/deploy_mujoco/deploy_mujoco_vision.py e3_vision.yaml
```

或：

```bash
cd /path/to/Humanoid_vision_mujoco/deploy_mujoco
python deploy_mujoco_vision.py configs/e3_vision.yaml
```

---

# 配置示例

```yaml
policy_path: "{DEPLOY_DIR}/policy/motion_lstm.pt"

xml_path: "{PACKAGE_ROOT}/resources/robots/e3_21dof/scene_terrain.xml"

simulation_duration: 600.0
simulation_dt: 0.002
control_decimation: 10

depth_size: [58, 87]
depth_render_size: [480, 640]

depth_min_range: 0.1
depth_max_range: 3.0

gamepad_type: logitech
```

---

# 目录速览

| 路径 | 说明 |
|------|------|
| `deploy_mujoco_vision.py` | 主入口 |
| `vision_deploy/paths.py` | `{DEPLOY_DIR}`、`{PACKAGE_ROOT}` 占位符展开 |
| `vision_deploy/policy_inference.py` | TorchScript 策略封装 |
| `vision_deploy/vision_depth.py` | 深度预处理 |
| `configs/*.yaml` | 仿真、PD、深度、策略路径等 |
| `policy/` | 放置 `motion_lstm.pt` |
| `utils/` | PD、重力方向、手柄、Viewer 辅助 |

---

# 路径占位符

| 占位符 | 含义 |
|---|---|
| `PACKAGE_ROOT` | 仓库根目录 `Humanoid_vision_mujoco` |
| `DEPLOY_DIR` | 当前目录 `deploy_mujoco` |

---

# 模块引用

已将：

```text
deploy_mujoco
```

加入 `sys.path` 后：

```python
from vision_deploy import (
    DEPLOY_DIR,
    VisionPolicyRunner,
    resolve_config_path,
)
```

---

# Viewer 与控制

Viewer 与手柄快捷键参考：

```text
utils/gamepad_utils.py
utils/viewer_utils.py
```

支持：

- Viewer 跟踪
- 重置机器人
- 深度图实时显示
- 手柄速度控制
- 相机调整

---

# 项目结构

```text
Humanoid_vision_mujoco/
├── deploy_mujoco/
│   ├── deploy_mujoco_vision.py
│   ├── configs/
│   ├── policy/
│   ├── vision_deploy/
│   └── utils/
│
├── resources/
│   └── robots/
│       └── e3_21dof/
│
└── README.md
```

---

# 注意事项

- 本项目为部署框架，不包含训练代码
- 默认使用 TorchScript (`*.pt`) 策略
- 不依赖 `legged_gym`
- 推荐 Linux 环境
- 推荐使用 NVIDIA GPU 进行高帧率深度渲染

---

# License

仅用于研究与学术用途。

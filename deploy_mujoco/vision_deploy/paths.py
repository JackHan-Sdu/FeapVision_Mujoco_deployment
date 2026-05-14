"""Standalone path helpers for MuJoCo deploy (no legged_gym)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, MutableMapping

# 本文件位于 deploy_mujoco/vision_deploy/
_VISION_DEPLOY = Path(__file__).resolve().parent
# deploy_mujoco/
DEPLOY_DIR: Path = _VISION_DEPLOY.parent
# Humanoid_vision_mujoco/
PACKAGE_ROOT: Path = DEPLOY_DIR.parent


def expand_placeholders(path_str: str) -> str:
    """Replace {DEPLOY_DIR}, {PACKAGE_ROOT} with absolute paths."""
    s = path_str.replace("{DEPLOY_DIR}", str(DEPLOY_DIR))
    s = s.replace("{PACKAGE_ROOT}", str(PACKAGE_ROOT))
    s = s.replace("{LEGGED_GYM_ROOT_DIR}", str(PACKAGE_ROOT))
    return s


def resolve_config_path(config_arg: str) -> Path:
    """Resolve CLI config to an existing YAML path."""
    p = Path(config_arg)
    if p.is_file():
        return p.resolve()
    cand = DEPLOY_DIR / "configs" / config_arg
    if cand.is_file():
        return cand.resolve()
    cand2 = DEPLOY_DIR / config_arg
    if cand2.is_file():
        return cand2.resolve()
    raise FileNotFoundError(
        f"Config not found: {config_arg!r}. Tried {cand} and {cand2}."
    )


def expand_config_paths(config: MutableMapping[str, Any]) -> None:
    """In-place expand policy_path, xml_path, and other string paths if present."""
    for key in ("policy_path", "xml_path", "gamepad_calibration_file"):
        if key in config and isinstance(config[key], str):
            config[key] = expand_placeholders(config[key])
            if key != "gamepad_calibration_file":
                config[key] = os.path.normpath(config[key])

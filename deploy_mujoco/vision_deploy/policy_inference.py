"""Load and run vision policies from TorchScript (JIT)."""
from __future__ import annotations

from typing import Any

import numpy as np
import torch


class VisionPolicyRunner:
    """Proprio obs + depth -> action via TorchScript."""

    def __init__(self, policy_path: str):
        self.policy_path = policy_path
        self._policy: Any = None
        self._load()

    def _load(self) -> None:
        self._policy = torch.jit.load(self.policy_path, map_location="cpu")
        self._policy.eval()
        print(f"Loaded PyTorch JIT: {self.policy_path}")

    def reset(self) -> None:
        if self._policy is not None and hasattr(self._policy, "reset"):
            self._policy.reset()

    def infer(self, obs: torch.Tensor, depth_obs: torch.Tensor) -> np.ndarray:
        """obs [1, D_obs], depth_obs [1, D_depth] -> action ndarray shape (num_actions,)"""
        out = self._policy(obs, depth_obs)
        return out.detach().numpy().squeeze()

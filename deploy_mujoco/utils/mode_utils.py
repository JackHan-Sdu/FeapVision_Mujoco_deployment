"""Command limits for gamepad (single profile: walking / vision deploy)."""
import numpy as np

# [max forward vx, max backward vx, max lateral vy, max yaw rate]
CMD_MAX = np.array([0.9, 0.8, 0.6, 1.5], dtype=np.float32)

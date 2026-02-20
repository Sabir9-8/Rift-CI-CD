"""
Rift Agent - AI-powered bug detection and fixing tool.
"""

__version__ = "1.0.0"
__author__ = "Rift Team"

from rift.agent import RiftAgent, FixResult
from rift.config import RiftConfig
from rift import utils

__all__ = [
    "RiftAgent", 
    "FixResult", 
    "RiftConfig",
    "utils",
]


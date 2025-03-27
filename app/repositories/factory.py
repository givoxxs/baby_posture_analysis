"""Repository factory module."""

from pathlib import Path
from functools import lru_cache
from app.config import settings
from app.repositories.base import FileRepository


@lru_cache()
def get_pose_repository():
    """Get the repository for pose detection results."""
    return FileRepository(settings.DATA_DIR, "poses")


@lru_cache()
def get_analysis_repository():
    """Get the repository for posture analysis results."""
    return FileRepository(settings.DATA_DIR, "analyses")

"""
Data models for pose detection.
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union


class Keypoint(BaseModel):
    """Model for a single keypoint."""
    id: int
    name: str
    x: float
    y: float
    z: float
    visibility: float


class PoseDetectionRequest(BaseModel):
    """Request model for pose detection."""
    high_resolution: bool = False
    include_annotated_image: bool = True
    include_analysis: bool = False


class PoseData(BaseModel):
    """Model for pose detection data."""
    keypoints: List[Keypoint]
    processing_time_ms: float
    total_processing_time_ms: float
    joint_angles: Optional[Dict[str, float]] = None


class PoseDetectionResponse(BaseModel):
    """Response model for pose detection."""
    keypoints_data: PoseData
    annotated_image: Optional[str] = None
    posture_analysis: Optional[Dict[str, Any]] = None
    message: str = "Pose detected successfully"

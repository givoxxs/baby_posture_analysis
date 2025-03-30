"""
Data models for posture analysis.
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class PostureFeatures(BaseModel):
    """Model for posture features."""
    head_angle: float
    arm_angles: Dict[str, float]
    leg_angles: Dict[str, float]
    torso_angle: float
    face_down: bool
    blanket_kicked: bool


class PostureAnalysisResponse(BaseModel):
    """Response model for posture analysis."""
    posture_type: str
    risk_score: float
    confidence: float
    details: Dict[str, bool]
    reasons: List[str]
    annotated_image: Optional[str] = None
    body_alignment: Optional[Dict[str, str]] = None
    issues: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

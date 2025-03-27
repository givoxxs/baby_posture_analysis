"""Pydantic models for API request and response validation."""

from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, Optional, Any, List
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level enum for posture analysis."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Point(BaseModel):
    """Representation of a 2D or 3D point with optional visibility score."""
    x: float = Field(..., description="X coordinate (0.0 to 1.0)")
    y: float = Field(..., description="Y coordinate (0.0 to 1.0)")
    z: Optional[float] = Field(None, description="Z coordinate (depth)")
    visibility: Optional[float] = Field(None, description="Visibility confidence score (0.0 to 1.0)")


class PostureAnalysis(BaseModel):
    """Detailed analysis of a detected posture."""
    face_position: Optional[str] = Field(None, description="Position of the face")
    limb_positions: Optional[List[str]] = Field(None, description="Positions of limbs")
    body_orientation: Optional[str] = Field(None, description="Overall body orientation")
    safety_concerns: Optional[List[str]] = Field(None, description="Identified safety concerns")
    recommendations: Optional[List[str]] = Field(None, description="Safety recommendations")


class PoseDetectionResponse(BaseModel):
    """Response model for pose detection endpoint."""
    landmarks: Dict[str, Point] = Field(
        ..., 
        description="Detected pose landmarks keyed by body part name"
    )
    pose_type: Optional[str] = Field(
        None, 
        description="Type of pose detected (e.g., lying_on_stomach, face_down)"
    )
    risk_level: Optional[RiskLevel] = Field(
        None, 
        description="Risk level of the detected pose"
    )
    risk_score: Optional[float] = Field(
        None, 
        ge=0, 
        le=10, 
        description="Numerical risk score (0-10)"
    )
    analysis: Optional[PostureAnalysis] = Field(
        None, 
        description="Detailed posture analysis"
    )
    image_url: Optional[str] = Field(
        None, 
        description="URL to the annotated image"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "landmarks": {
                    "nose": {"x": 0.5, "y": 0.3, "z": 0.1, "visibility": 0.98},
                    "left_shoulder": {"x": 0.4, "y": 0.5, "z": 0.2, "visibility": 0.95}
                },
                "pose_type": "lying_on_stomach",
                "risk_level": "medium",
                "risk_score": 5.7,
                "analysis": {
                    "face_position": "turned_to_side",
                    "limb_positions": ["arms_extended", "legs_folded"],
                    "body_orientation": "prone",
                    "safety_concerns": ["partial face obstruction"],
                    "recommendations": ["monitor breathing", "consider repositioning"]
                },
                "image_url": "/static/processed_images/img_12345.jpg"
            }
        }
    }


class PoseDetectionRequest(BaseModel):
    """Request model for pose detection settings."""
    high_resolution: bool = Field(
        False, 
        description="Use high resolution processing"
    )
    include_annotated_image: bool = Field(
        True, 
        description="Include annotated image in response"
    )
    include_analysis: bool = Field(
        False, 
        description="Include detailed posture analysis"
    )

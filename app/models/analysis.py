"""Models for analysis results."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from app.models.schemas import RiskLevel, PostureAnalysis, Point


class PoseAnalysisRecord(BaseModel):
    """Model for storing pose analysis results."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Time of analysis")
    pose_type: Optional[str] = Field(None, description="Type of pose detected")
    risk_level: Optional[RiskLevel] = Field(None, description="Risk level of the detected pose")
    risk_score: Optional[float] = Field(None, description="Numerical risk score (0-10)")
    analysis: Optional[PostureAnalysis] = Field(None, description="Detailed posture analysis")
    image_path: Optional[str] = Field(None, description="Path to the original image")
    annotated_image_path: Optional[str] = Field(None, description="Path to the annotated image")
    landmarks: Optional[Dict[str, Point]] = Field(None, description="Key pose landmarks")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
                "timestamp": "2023-04-15T12:30:45",
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
                "image_path": "/static/uploads/img_12345.jpg",
                "annotated_image_path": "/static/processed_images/img_12345.jpg",
                "landmarks": {
                    "nose": {"x": 0.5, "y": 0.3, "z": 0.1, "visibility": 0.98}
                }
            }
        }
    }

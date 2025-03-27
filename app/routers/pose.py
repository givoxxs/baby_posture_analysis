"""
Pose detection router.

This module contains the API endpoints for detecting and analyzing poses in images.
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, Request, Query
from fastapi.responses import JSONResponse
from typing import Optional
import traceback
import logging

from app.services.pose_service import PoseService
from app.services.service_factory import get_pose_service
from app.utils.error_handling import handle_exceptions, ProcessingError, ValidationError
from app.models.schemas import PoseDetectionResponse, PoseDetectionRequest

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/pose",
    tags=["pose detection"]
)


@router.post("/detect", response_model=PoseDetectionResponse)
@handle_exceptions
async def detect_pose(
    file: UploadFile = File(...),
    high_resolution: bool = Form(False),
    include_annotated_image: bool = Form(True),
    include_analysis: bool = Form(False),
    pose_service: PoseService = Depends(get_pose_service)
):
    """
    Detect pose in the uploaded image.
    
    This endpoint analyzes an image to detect human pose landmarks and returns
    various analysis results including the pose type and risk assessment.
    
    Parameters:
    - file: Image file to analyze
    - high_resolution: Whether to use high resolution processing
    - include_annotated_image: Whether to include annotated image in response
    - include_analysis: Whether to include detailed posture analysis
    
    Returns:
    - PoseDetectionResponse: Object containing detected landmarks and analysis
    """
    try:
        # Validate file type
        content_type = file.content_type or ""
        if not content_type.startswith("image/"):
            raise ValidationError(
                f"Unsupported file type: {content_type}. Only images are supported.",
                {"supported_types": ["image/jpeg", "image/png", "image/bmp"]}
            )
        
        logger.info(
            f"Processing image for pose detection: {file.filename}, "
            f"high_res={high_resolution}, include_image={include_annotated_image}, "
            f"include_analysis={include_analysis}"
        )
        
        result = await pose_service.process_image(
            file=file,
            high_resolution=high_resolution,
            include_annotated_image=include_annotated_image,
            include_analysis=include_analysis
        )
        
        logger.info(f"Pose detection completed for {file.filename}")
        return result
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in pose detection: {str(e)}\n{error_details}")
        raise ProcessingError(
            f"Error detecting pose: {str(e)}",
            {"filename": file.filename} if file else {}
        )


@router.get("/info")
async def get_pose_detection_info():
    """
    Get information about the pose detection service.
    
    Returns details about the available pose types, supported image formats,
    and other relevant information.
    
    Returns:
    - Dictionary containing service information
    """
    return {
        "supported_file_types": ["image/jpeg", "image/png", "image/bmp"],
        "pose_types": [
            "lying_on_back", 
            "lying_on_stomach", 
            "lying_on_side",
            "face_down"
        ],
        "risk_levels": ["low", "medium", "high", "critical"],
        "max_file_size_mb": 10,
        "recommended_resolution": "640x480 or higher"
    }

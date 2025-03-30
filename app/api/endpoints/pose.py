"""
API endpoints for pose detection.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from typing import Optional
import traceback

from app.services.pose_service import PoseService

router = APIRouter(
    prefix="/api/pose",
    tags=["pose detection"]
)

# Dependency to get pose service
def get_pose_service():
    """Dependency for getting the pose service instance."""
    return PoseService()


@router.post("/detect")
async def detect_pose(
    file: UploadFile = File(...),
    high_resolution: bool = Form(False),
    include_annotated_image: bool = Form(True),
    include_analysis: bool = Form(False),
    pose_service: PoseService = Depends(get_pose_service)
):
    """
    Detect pose from an uploaded image.
    
    - **file**: Image file
    - **high_resolution**: Whether to use high resolution processing
    - **include_annotated_image**: Whether to include the annotated image in the response
    - **include_analysis**: Whether to include posture analysis in the response
    """
    try:
        result = await pose_service.detect_pose(
            file=file,
            high_resolution=high_resolution,
            include_annotated_image=include_annotated_image,
            include_analysis=include_analysis
        )
        
        return result
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error detecting pose: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error detecting pose: {str(e)}"
        )

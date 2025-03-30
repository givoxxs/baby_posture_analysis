"""
API endpoints for posture analysis.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import json
import traceback

from app.services.posture_service import PostureService
from app.services.pose_service import PoseService

router = APIRouter(
    prefix="/api/posture",
    tags=["posture analysis"]
)

# Dependencies for services
def get_posture_service():
    """Dependency for getting the posture service instance."""
    return PostureService()

def get_pose_service():
    """Dependency for getting the pose service instance."""
    return PoseService()


@router.post("/analyze")
async def analyze_posture(
    file: UploadFile = File(...),
    pose_service: PoseService = Depends(get_pose_service),
    posture_service: PostureService = Depends(get_posture_service)
):
    """
    Analyze posture from an uploaded image.
    
    1. Detects pose using MediaPipe
    2. Extracts posture features
    3. Analyzes risk level
    """
    try:
        # Detect pose first
        pose_result = await pose_service.detect_pose(
            file=file,
            high_resolution=True,
            include_annotated_image=True,
            include_analysis=False
        )
        
        if "keypoints_data" not in pose_result or not pose_result["keypoints_data"].get("keypoints"):
            return JSONResponse(
                status_code=400,
                content={"error": "No person detected in the image"}
            )
        
        # Analyze posture using detected keypoints
        posture_analysis = posture_service.analyze_from_keypoints(pose_result["keypoints_data"])
        
        # Include annotated image in the response if available
        if "annotated_image" in pose_result:
            posture_analysis["annotated_image"] = pose_result["annotated_image"]
        
        return posture_analysis
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error analyzing posture: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error analyzing posture: {str(e)}"
        )


@router.post("/analyze-keypoints")
async def analyze_posture_from_keypoints(
    keypoints_data: Dict[str, Any],
    posture_service: PostureService = Depends(get_posture_service)
):
    """
    Analyze posture from keypoints data directly.
    
    This endpoint is useful for analyzing poses that have already been detected.
    """
    try:
        posture_analysis = posture_service.analyze_from_keypoints(keypoints_data)
        return posture_analysis
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error analyzing posture from keypoints: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error analyzing posture from keypoints: {str(e)}"
        )

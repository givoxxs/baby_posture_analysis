"""
API endpoints for pose detection.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import traceback

from app.services.pose_service import PoseService

# Dependency to get PoseService instance
def get_pose_service():
    return PoseService()

router = APIRouter(
    prefix="/api/pose",
    tags=["pose"]
)

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

@router.post("/analyze")
async def analyze_posture(
    file: UploadFile = File(...),
    high_resolution: bool = Form(False),
    pose_service: PoseService = Depends(get_pose_service)
):
    """
    Analyze baby posture from an uploaded image.
    
    - **file**: Image file
    - **high_resolution**: Whether to use high resolution processing
    """
    try:
        result = await pose_service.analyze_posture(
            file=file,
            high_resolution=high_resolution
        )
        
        # Add confidence field for frontend compatibility
        if result["success"]:
            result["confidence"] = 95.0  # Sample confidence value
        
        return result
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error analyzing posture: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error analyzing posture: {str(e)}"
        )

@router.post("/posture/analyze")
async def analyze_baby_posture(
    file: UploadFile = File(...),
    high_resolution: bool = Form(False),
    pose_service: PoseService = Depends(get_pose_service)
):
    """
    Complete endpoint for baby posture analysis (for frontend)
    
    - **file**: Image file
    - **high_resolution**: Whether to use high resolution processing
    """
    try:
        result = await pose_service.analyze_posture(
            file=file,
            high_resolution=high_resolution
        )
        
        # Format for frontend
        if result["success"]:
            return {
                "posture_type": result["posture_type"],
                "risk_score": result["risk_score"],
                "confidence": 95.0,  # Sample confidence value
                "reasons": result["reasons"],
                "annotated_image": result["annotated_image"],
                "processing_time_ms": result["processing_time_ms"],
                "recommendations": [
                    "Make sure baby sleeps on their back",
                    "Keep the sleeping area free from blankets and toys",
                    "Monitor baby frequently during sleep"
                ]
            }
        else:
            return {
                "success": False,
                "message": result.get("message", "Failed to analyze posture")
            }
            
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error analyzing baby posture: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error analyzing baby posture: {str(e)}"
        )

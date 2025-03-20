from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from typing import Optional
import traceback

from app.services.pose_service import PoseService
from app.services.image_service import ImageService
from app.utils.mediapipe_utils import PoseDetector

router = APIRouter(
    prefix="/api/pose",
    tags=["pose detection"]
)

# Dependency to get pose service
def get_pose_service():
    """Dependency for getting the pose service instance"""
    image_service = ImageService()
    pose_detector = PoseDetector(
        static_image_mode=True,
        model_complexity=2,
        min_detection_confidence=0.5
    )
    return PoseService(image_service=image_service, pose_detector=pose_detector)

@router.post("/detect")
async def detect_pose(
    file: UploadFile = File(...),
    high_resolution: bool = Form(False),
    include_annotated_image: bool = Form(True),
    include_analysis: bool = Form(False),
    pose_service: PoseService = Depends(get_pose_service)
):
    """
    Detect pose in an uploaded image
    
    - **file**: Image file to process
    - **high_resolution**: Whether to use higher resolution for better accuracy
    - **include_annotated_image**: Whether to include the annotated image in the response
    - **include_analysis**: Whether to include posture analysis in the response
    """
    try:
        # Detect pose
        result = await pose_service.detect_pose_from_file(
            file=file,
            high_resolution=high_resolution,
            include_annotated_image=include_annotated_image
        )
        
        # Include posture analysis if requested
        if include_analysis:
            analysis = pose_service.analyze_posture(result["keypoints_data"])
            result["posture_analysis"] = analysis
        
        return result
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error detecting pose: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error detecting pose: {str(e)}"
        )

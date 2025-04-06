from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from typing import Optional
import traceback
import logging # Import logging

from app.services.pose_service import PoseService, get_singleton_pose_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/pose",
    tags=["pose"]
)

@router.post("/detect")
async def detect_pose(
    file: UploadFile = File(...),
    include_annotated_image: bool = Form(True),
    include_analysis: bool = Form(False),
    pose_service: PoseService = Depends(get_singleton_pose_service)
):
    try:
        result = await pose_service.detect_pose(
            file=file,
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
    pose_service: PoseService = Depends(get_singleton_pose_service)
):
    try:
        # Get full posture analysis
        result = await pose_service.analyze_posture(
            file=file
        )

        if not result.get("success"):
            logger.warning(f"Pipeline analysis failed for {file.filename}: {result.get('message')}")
            # Trả về lỗi với thông báo từ service
            raise HTTPException(
                status_code=422, # Unprocessable Entity hoặc mã lỗi phù hợp khác
                detail=result.get("message", "Analysis failed")
            )
        
        # Structure response in a user-friendly format
        if result["success"]:
            response = {
                "success": True,
                "posture": {
                    "position": result['analysis']["position"],
                    "is_covered": result['analysis']["is_covered"],
                    "risk_level": result['analysis']["risk_level"],
                    "unnatural_limbs": result['analysis']["unnatural_limbs"],
                    "risk_score": result['analysis']["risk_score"],
                    "confidence": result['analysis']["confidence"],
                    "reasons": result['analysis']["reasons"],
                    "recommendations": result['analysis']["recommendations"],
                },
                "image": {
                    "annotated": result["annotated_image"],
                    "processing_time_ms": result["processing_time_ms"]
                },
                "image_dimensions": {
                    "width": result["image_dimensions"]["width"],
                    "height": result["image_dimensions"]["height"]
                }
            }
        else:
            response = {
                "success": False,
                "message": result.get("message", "Failed to analyze posture")
            }
        
        return JSONResponse(content=response)
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in image pipeline: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error in image pipeline: {str(e)}"
        )

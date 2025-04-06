from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends # type: ignore
from fastapi.responses import JSONResponse # type: ignore
import traceback
from app.services.pose_service import PoseService

router = APIRouter(
    prefix="/api/pipeline",
    tags=["pipeline"]
)

pose_service_instance = PoseService()

def get_singleton_pose_service():
    return pose_service_instance

@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    pose_service: PoseService = Depends(get_singleton_pose_service)
):
    try:
        # Get full posture analysis
        result = await pose_service.analyze_posture(
            file=file
        )
        
        # Structure response in a user-friendly format
        if result["success"]:
            response = {
                "success": True,
                "posture": {
                    "type": result["posture_type"],
                    "risk_score": result["risk_score"],
                    "reasons": result["reasons"]
                },
                "image": {
                    "annotated": result["annotated_image"],
                    "processing_time_ms": result["processing_time_ms"]
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

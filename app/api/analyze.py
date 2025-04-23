from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from typing import Optional
import traceback
import logging
from datetime import datetime

from app.services.analysis_service import AnalysisService, get_singleton_analysis_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/analyze",
    tags=["analyze"]
)

@router.post("/posture")
async def analyze_baby_posture(
    file: UploadFile = File(...),
    timestamp: Optional[str] = Query(None, description="Timestamp of the image in ISO format (YYYY-MM-DDTHH:MM:SS.sssZ). If not provided, current time will be used."),
    analysis_service: AnalysisService = Depends(get_singleton_analysis_service)
):
    """
    Analyze a baby's posture from an uploaded image
    
    Parameters:
    - file: Image file to analyze
    - timestamp: Optional timestamp for the image
    
    Returns:
    - Complete analysis including posture classification, face covering detection, and blanket covering detection
    """
    try:
        # Validate timestamp if provided
        if timestamp:
            try:
                # Attempt to parse timestamp to validate format
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                return JSONResponse(
                    status_code=422,
                    content={
                        "success": False,
                        "message": "Invalid timestamp format. Please use ISO format (YYYY-MM-DDTHH:MM:SS.sssZ)."
                    }
                )

        # Process the image using our service
        result = await analysis_service.analyze_image(file, timestamp)
        logger.info("="*50)
        logger.info(f"Image analysis result:")
        if result.get("success"):
            logger.info(f"Success: {result.get('success')}")
            logger.info(f"Posture: {result.get('analysis', {}).get('position')}")
            logger.info(f"Face: {result.get('analysis', {}).get('face_covered')}")
            logger.info(f"Blanket: {result.get('analysis', {}).get('is_covered')}")
            logger.info(f"Image dimensions: {result.get('image_dimensions')}")
            logger.info(f"Processing time (ms): {result.get('processing_time_ms')}")
            logger.info(f"Image filename: {file.filename}")
        else:
            logger.info(f"Success: {result.get('success')}")
            logger.info(f"Message: {result.get('message')}")
            logger.info(f"Image filename: {file.filename}")
        logger.info(f"Timestamp: {result.get('timestamp')}") 
        logger.info("="*50)

        if not result.get("success"):
            logger.warning(f"Analysis failed for {file.filename}: {result.get('message')}")
            return JSONResponse(
                status_code=422,
                content=result
            )
        
        # Structure response in a user-friendly format
        response = {
            "success": True,
            "timestamp": result["timestamp"],
            "posture": {
                "position": result['analysis']["position"],
                "position_id": result['analysis']["position_id"],
                "probabilities": result['analysis']["probabilities"],
            },
            # "face": {
            #     "is_covered": result['analysis']["face_covered"],
            #     "confidence": result['analysis']["face_confidence"]
            # },
            "blanket": {
                "is_covered": result['analysis']["is_covered"],
                "coverage_ratio": result['analysis']["coverage_ratio"]
            },
            "image": {
                "annotated": result["annotated_image"],
                "processing_time_ms": result["processing_time_ms"]
            },
            "image_dimensions": result["image_dimensions"]
        }
        print(f"Success: ", response["success"])
        print(f"Timestamp: ", response["timestamp"])
        print(f"Posture: ", response["posture"])
        # print(f"Face: ", response["face"])
        print(f"Blanket: ", response["blanket"])
        print(f"Image Dimensions: ", response["image_dimensions"])
        
        return JSONResponse(content=response)
    
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in baby posture analysis: {str(e)}\n{error_details}")
        return JSONResponse(
            status_code=500, 
            content={
                "success": False,
                "message": f"Error in baby posture analysis: {str(e)}"
            }
        )

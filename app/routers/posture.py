"""API router for posture analysis endpoints."""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import Response
import json
from typing import Dict, Any, List, Optional
import numpy as np

from app.services.posture_service import PostureService

router = APIRouter(
    prefix="/posture",
    tags=["posture"],
    responses={404: {"description": "Not found"}},
)

# Create PostureService instance
posture_service = PostureService()

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles NumPy arrays."""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.float32) or isinstance(obj, np.float64):
            return float(obj)
        if isinstance(obj, np.int32) or isinstance(obj, np.int64):
            return int(obj)
        if isinstance(obj, dict):
            return {k: self.default(v) for k, v in obj.items()}
        if isinstance(obj, list) or isinstance(obj, tuple):
            return [self.default(i) for i in obj]
        return json.JSONEncoder.default(self, obj)

@router.post("/analyze")
async def analyze_posture_from_image(file: UploadFile = File(...)):
    """
    Analyze baby posture from an uploaded image.
    
    Args:
        file: Uploaded image file
    
    Returns:
        Posture analysis results including keypoints and features
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read the file content
    image_data = await file.read()
    
    # Process the image
    result = await posture_service.process_image(image_data)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    # Serialize the result data (excluding the annotated image)
    analysis_result = {
        "success": result["success"],
        "message": result["message"],
        "keypoints": result["keypoints"],
        "features": result["features"]
    }
    
    # Convert NumPy arrays to standard Python types for JSON serialization
    serialized_result = json.dumps(analysis_result, cls=NumpyEncoder)
    
    return Response(content=serialized_result, media_type="application/json")

@router.post("/annotated-image")
async def get_annotated_image(file: UploadFile = File(...)):
    """
    Process an image and return the annotated version with pose keypoints.
    
    Args:
        file: Uploaded image file
    
    Returns:
        Annotated image with pose keypoints visualized
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read the file content
    image_data = await file.read()
    
    # Process the image
    result = await posture_service.process_image(image_data)
    
    if not result["success"] or "annotated_image" not in result:
        raise HTTPException(status_code=400, detail=result["message"])
    
    # Return the annotated image
    return Response(content=result["annotated_image"], media_type="image/jpeg")

@router.post("/analyze-keypoints")
async def analyze_posture_from_keypoints(keypoints: List[List[float]]):
    """
    Analyze baby posture from provided keypoints.
    
    Args:
        keypoints: List of pose keypoints [x, y, z, visibility]
    
    Returns:
        Posture features extracted from the keypoints
    """
    if not keypoints or len(keypoints) == 0:
        raise HTTPException(status_code=400, detail="No keypoints provided")
    
    # Process the keypoints
    result = posture_service.analyze_posture(keypoints)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    # Convert NumPy arrays to standard Python types for JSON serialization
    serialized_result = json.dumps(result, cls=NumpyEncoder)
    
    return Response(content=serialized_result, media_type="application/json")

@router.post("/interpret")
async def interpret_posture(features: Dict[str, Any]):
    """
    Interpret the posture features to determine baby's posture.
    
    Args:
        features: Dictionary of posture features
    
    Returns:
        Interpretation of the baby's posture
    """
    # Interpret the features
    interpretation = posture_service.interpret_posture(features)
    
    return interpretation

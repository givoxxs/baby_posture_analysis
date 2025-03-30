"""
API endpoints for image processing.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import traceback

from app.core.models.image import Base64ImageRequest, ImageProcessingResponse
from app.services.image_service import ImageService

router = APIRouter(
    prefix="/api/images",
    tags=["image processing"]
)

# Dependency to get the image service
def get_image_service():
    """Dependency for getting the image service instance."""
    return ImageService()


@router.post("/process-upload")
async def process_uploaded_image(
    file: UploadFile = File(...),
    apply_resize: bool = Form(True),
    apply_normalize: bool = Form(True),
    apply_filter: bool = Form(True),
    filter_type: str = Form("gaussian"),
    image_service: ImageService = Depends(get_image_service)
):
    """Process an uploaded image file with standard processing."""
    try:
        return await image_service.process_uploaded_image(
            file=file,
            apply_resize=apply_resize,
            apply_normalize=apply_normalize,
            apply_filter=apply_filter,
            filter_type=filter_type
        )
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error processing image: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing image: {str(e)}"
        )


@router.post("/process-base64")
async def process_base64_image(
    request: Base64ImageRequest,
    image_service: ImageService = Depends(get_image_service)
):
    """Process an image provided as base64 string."""
    try:
        # Implementation will be similar to process_uploaded_image but for base64
        # This would be implemented in the ImageService
        raise HTTPException(
            status_code=501, 
            detail="Base64 image processing not implemented yet"
        )
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error processing base64 image: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing base64 image: {str(e)}"
        )


@router.post("/process-mediapipe")
async def process_for_mediapipe(
    file: UploadFile = File(...),
    high_resolution: bool = Form(False),
    image_service: ImageService = Depends(get_image_service)
):
    """Process an uploaded image with optimizations for MediaPipe."""
    try:
        return await image_service.optimize_for_mediapipe(
            file=file,
            high_resolution=high_resolution
        )
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error processing image for MediaPipe: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing image for MediaPipe: {str(e)}"
        )

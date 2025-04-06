"""
API endpoints for image processing.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Union, Dict, Any
import traceback

import numpy as np

from app.services.image_service import ImageService

router = APIRouter(
    prefix="/api/images",
    tags=["images"]
)

# Dependency to get the image service
def get_image_service():
    """Dependency for getting the image service instance."""
    return ImageService()

@router.post("/process")
async def process_image(
    file: UploadFile = File(...),
    high_resolution: bool = Form(True),
    apply_filter: bool = Form(True)
):
    try:
        result = await ImageService().process_image(
            file=file,
            high_resolution=high_resolution,
            apply_noise_filter=apply_filter
        )
        
        return JSONResponse(content=result)
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error processing image: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing image: {str(e)}"
        )

@router.post("/process-upload")
async def process_uploaded_image(
    file: UploadFile = File(...),
    apply_resize: bool = Form(True),
    apply_normalize: bool = Form(True),
    apply_filter: bool = Form(True),
    filter_type: str = Form("gaussian"),
    image_service: ImageService = Depends(get_image_service)
):
    try:
        # Use process_image instead since that's what we have implemented
        result = await image_service.process_image(
            file=file,
            high_resolution=True,
            apply_noise_filter=apply_filter
        )
        return result
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error processing image: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing image: {str(e)}"
        )

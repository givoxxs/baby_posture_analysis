from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Union
import numpy as np

from app.utils.image_utils import ImagePreProcessor

router = APIRouter(
    prefix="/api/images",
    tags=["image processing"]
)

class Base64ImageRequest(BaseModel):
    image: str
    apply_resize: bool = True
    apply_normalize: bool = True
    apply_filter: bool = True
    filter_type: str = "gaussian"

# Dependency to get the image processor
def get_image_processor():
    return ImagePreProcessor(width=640, height=480)

@router.post("/process-upload")
async def process_uploaded_image(
    file: UploadFile = File(...),
    apply_resize: bool = Form(True),
    apply_normalize: bool = Form(True),
    apply_filter: bool = Form(True),
    filter_type: str = Form("gaussian"),
    processor: ImagePreProcessor = Depends(get_image_processor)
):
    """
    Process an uploaded image file
    """
    try:
        # Verify file is an image
        content_type = file.content_type
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Process the image
        processed_image = await processor.preprocess_image(
            file,
            apply_resize=apply_resize,
            apply_normalize=apply_normalize,
            apply_filter=apply_filter,
            filter_type=filter_type
        )
        
        # Convert processed image to base64
        base64_image = processor.to_base64(processed_image)
        
        return {
            "message": "Image processed successfully",
            "processed_image": base64_image,
            "width": processor.width,
            "height": processor.height
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@router.post("/process-base64")
async def process_base64_image(
    request: Base64ImageRequest,
    processor: ImagePreProcessor = Depends(get_image_processor)
):
    """
    Process an image provided as base64 string
    """
    try:
        if not request.image:
            raise HTTPException(status_code=400, detail="Base64 image data is required")
        
        # Process the image
        processed_image = await processor.preprocess_image(
            request.image,
            apply_resize=request.apply_resize,
            apply_normalize=request.apply_normalize,
            apply_filter=request.apply_filter,
            filter_type=request.filter_type
        )
        
        # Convert processed image to base64
        base64_image = processor.to_base64(processed_image)
        
        return {
            "message": "Image processed successfully",
            "processed_image": base64_image,
            "width": processor.width,
            "height": processor.height
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

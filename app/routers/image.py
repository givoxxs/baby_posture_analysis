from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Union
import numpy as np
import time
import os

from app.utils.image_utils import ImagePreProcessor

# Setup templates directory
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))

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

@router.get("/index_2", response_class=HTMLResponse)
async def get_index2(request: Request):
    """Render index_2 template"""
    return templates.TemplateResponse("index_2.html", {"request": request})

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
        start_time = time.time()
        
        # Verify file is an image
        content_type = file.content_type
        if not content_type or not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"File must be an image, got {content_type}")
            
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
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            "message": "Image processed successfully",
            "processed_image": base64_image,
            "width": processor.width,
            "height": processor.height,
            "processing_time_ms": round(processing_time, 2)
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing image: {str(e)}\n{error_details}")
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

@router.post("/process-mediapipe")
async def process_for_mediapipe(
    file: UploadFile = File(...),
    high_resolution: bool = Form(False),
    processor: ImagePreProcessor = Depends(get_image_processor)
):
    """
    Process an uploaded image with optimizations for MediaPipe
    """
    try:
        start_time = time.time()
        
        # Verify file is an image
        content_type = file.content_type
        if not content_type or not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"File must be an image, got {content_type}")
            
        # Process the image with MediaPipe optimizations
        processed_image = await processor.preprocess_for_mediapipe(
            file,
            high_resolution=high_resolution
        )
        
        # Convert processed image to base64
        base64_image = processor.to_base64(processed_image)
        
        # Get dimensions
        width = 1280 if high_resolution else processor.width
        height = 720 if high_resolution else processor.height
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            "message": "Image processed for MediaPipe successfully",
            "processed_image": base64_image,
            "width": width,
            "height": height,
            "processing_time_ms": round(processing_time, 2)
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing image for MediaPipe: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing image for MediaPipe: {str(e)}"
        )

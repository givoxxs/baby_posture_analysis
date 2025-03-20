from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Union
import traceback

from app.services.image_service import ImageService
from app.utils.image_preprocessor import ImagePreProcessor

# Setup templates directory
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))

router = APIRouter(
    prefix="/api/images",
    tags=["image processing"]
)

class Base64ImageRequest(BaseModel):
    """Request model for base64 image processing"""
    image: str
    apply_resize: bool = True
    apply_normalize: bool = True
    apply_filter: bool = True
    filter_type: str = "gaussian"

# Dependency to get image service
def get_image_service():
    """Dependency for getting the image service instance"""
    processor = ImagePreProcessor(width=640, height=480)
    return ImageService(processor=processor)

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
    image_service: ImageService = Depends(get_image_service)
):
    """Process an uploaded image file with standard processing"""
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
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@router.post("/process-base64")
async def process_base64_image(
    request: Base64ImageRequest,
    image_service: ImageService = Depends(get_image_service)
):
    """Process an image provided as base64 string"""
    try:
        return await image_service.process_base64_image(
            base64_str=request.image,
            apply_resize=request.apply_resize,
            apply_normalize=request.apply_normalize,
            apply_filter=request.apply_filter,
            filter_type=request.filter_type
        )
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error processing base64 image: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@router.post("/process-mediapipe")
async def process_for_mediapipe(
    file: UploadFile = File(...),
    high_resolution: bool = Form(False),
    image_service: ImageService = Depends(get_image_service)
):
    """Process an uploaded image with optimizations for MediaPipe"""
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

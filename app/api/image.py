"""
API endpoints for image processing.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Union, Dict, Any
import traceback

import numpy as np

from app.services.image_service import ImageService, get_image_service

router = APIRouter(
    prefix="/api/images",
    tags=["images"]
)

@router.post("/process")
async def process_image(
    file: UploadFile = File(...),
    image_service: ImageService = Depends(get_image_service)
):
    try:
        result = await image_service.process_image(
            file=file,
        )
        
        return JSONResponse(content=result)
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error processing image: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing image: {str(e)}"
        )

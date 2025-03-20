from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Union
import numpy as np

from app.utils.image_utils import ImagePreProcessor

from app.utils.image_utils import ImagePreProcessor

router = APIRouter(
    prefix="/api/images_pipeline",
    tags=["image pipeline"]
)

# api nhận ảnh từ phía người dùng xử lý nhiều quá trình bao gồm nhận ảnh vào -> tiền xử lý ảnh -> phân tích ảnh -> trả về kết quả tư thế của trẻ
# trước mắt áp dụng quá trình nhận ảnh vào -> tiền xử lý ảnh vào pipeline hiện tại

class Base64ImageRequest(BaseModel):
    image: str
    apply_resize: bool = True
    apply_normalize: bool = True
    apply_filter: bool = True
    filter_type: str = "gaussian"

# Dependency to get the image processor
def get_image_processor():
    return ImagePreProcessor(width=640, height=480)

@router.post("/analysis")
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
        if not content_type or not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"File must be an image, got {content_type}")
            
        # Debug information
        print(f"Processing file: {file.filename}, type: {type(file)}, content type: {content_type}")
        
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
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
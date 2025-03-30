"""
Data models for image processing.
"""

from pydantic import BaseModel
from typing import Optional, List


class ImageProcessingRequest(BaseModel):
    """Request model for image processing."""
    apply_resize: bool = True
    apply_normalize: bool = True
    apply_filter: bool = True
    filter_type: str = "gaussian"


class Base64ImageRequest(BaseModel):
    """Request model for processing a base64-encoded image."""
    image: str
    apply_resize: bool = True
    apply_normalize: bool = True
    apply_filter: bool = True
    filter_type: str = "gaussian"


class ImageProcessingResponse(BaseModel):
    """Response model for image processing."""
    processed_image: str
    width: int
    height: int
    processing_time_ms: float
    message: str = "Image processed successfully"

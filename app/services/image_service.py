"""
Service for image processing operations.
"""

import cv2
import numpy as np
import base64
from fastapi import UploadFile
from typing import Dict, Any, Union
import time

from app.utils.image_utils import (
    load_image, 
    load_image_from_base64,
    resize_image, 
    normalize_colors, 
    filter_noise, 
    to_base64, 
    enhance_for_pose_detection
)
from app.config import settings


class ImageService:
    """Service for handling image processing operations."""
    
    async def process_uploaded_image(
        self, 
        file: UploadFile,
        apply_resize: bool = True,
        apply_normalize: bool = True,
        apply_filter: bool = True,
        filter_type: str = "gaussian"
    ) -> Dict[str, Any]:
        """Process an uploaded image with standard processing."""
        # Load image
        image = await load_image(file)
        original_height, original_width = image.shape[:2]
        
        # Process image
        start_time = time.time()
        
        if apply_resize:
            image = resize_image(image, width=640, height=480)
            
        if apply_filter:
            image = filter_noise(image, filter_type=filter_type)
            
        if apply_normalize:
            image = normalize_colors(image)
            
        end_time = cv2.getTickCount()
        processing_time_ms = (end_time - start_time) * 1000 / cv2.getTickFrequency()
        
        # Get final dimensions
        height, width = image.shape[:2]
        
        # Convert to base64
        base64_image = to_base64(image)
        
        return {
            "processed_image": base64_image,
            "width": width,
            "height": height,
            "original_width": original_width,
            "original_height": original_height,
            "processing_time_ms": processing_time_ms,
        }
    
    async def process_base64_image(
        self, 
        base64_string: str,
        apply_resize: bool = True,
        apply_normalize: bool = True,
        apply_filter: bool = True,
        filter_type: str = "gaussian"
    ) -> Dict[str, Any]:
        """Process an image provided as base64 string."""
        # Load image from base64
        image = load_image_from_base64(base64_string)
        
        # Process image
        return await self.process_uploaded_image(
            file=image,
            apply_resize=apply_resize,
            apply_normalize=apply_normalize,
            apply_filter=apply_filter,
            filter_type=filter_type
        )

    
    async def optimize_for_mediapipe(
        self,
        image_source: Union[UploadFile, str, np.ndarray],
        high_resolution: bool = False
    )  -> Dict[str, Any]:
        """Process an image with optimizations for MediaPipe."""
        # Load image
        if hasattr(image_source, "read") and callable(getattr(image_source, "read")):
            # This is likely a file-like object such as UploadFile
            image = await load_image(image_source)
        elif isinstance(image_source, str):
            image = load_image_from_base64(image_source)
        elif isinstance(image_source, np.ndarray):
            image = image_source
        else:
            raise ValueError(f"Unsupported image source type: {type(image_source)}")
        # Process for MediaPipe
        start_time = cv2.getTickCount() 
        
        # Resize based on resolution setting
        if high_resolution:
            image = resize_image(image, width=1280, height=720)
        else:
            image = resize_image(image, width=settings.IMAGE_WIDTH, height=settings.IMAGE_HEIGHT)

        image = filter_noise(image, filter_type="median", kernel_size=3)
         
        image = normalize_colors(image)

        image = enhance_for_pose_detection(image)
        
        end_time = cv2.getTickCount()
        processing_time_ms = (end_time - start_time) * 1000 / cv2.getTickFrequency()
        
        # Get final dimensions
        height, width = image.shape[:2]
        
        return {
            "processed_image": image,
            "width": width,
            "height": height,
            "processing_time_ms": processing_time_ms,
        }

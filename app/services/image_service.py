"""
Service for image processing operations.
"""

import cv2
import numpy as np
import base64
from fastapi import UploadFile
from typing import Dict, Any, Union

from app.utils.image_utils import load_image, resize_image, normalize_colors, filter_noise, to_base64
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
        start_time = cv2.getTickCount()
        
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
    
    async def optimize_for_mediapipe(
        self,
        file: UploadFile,
        high_resolution: bool = False
    ) -> Dict[str, Any]:
        """Process an image with optimizations for MediaPipe."""
        # Load image
        image = await load_image(file)
        
        # Process for MediaPipe
        start_time = cv2.getTickCount()
        
        # Resize based on resolution setting
        if high_resolution:
            image = resize_image(image, width=1280, height=720)
        else:
            image = resize_image(image, width=settings.IMAGE_WIDTH, height=settings.IMAGE_HEIGHT)
            
        # Apply median filter for noise reduction
        image = filter_noise(image, filter_type="median", kernel_size=3)
        
        # Enhance contrast for better detection
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        enhanced_lab = cv2.merge((cl, a, b))
        image = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
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
            "processing_time_ms": processing_time_ms,
        }

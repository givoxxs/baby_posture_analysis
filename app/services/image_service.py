"""
Service for image processing operations.
"""

import cv2
import numpy as np
import base64
from fastapi import UploadFile
from typing import Dict, Any, Union, Optional

from app.utils.image_preprocessing import preprocess_image, image_to_base64


class ImageService:
    """Service for handling image processing operations."""
    
    async def process_image(
        self,
        file: UploadFile,
    ) -> Dict[str, Any]:

        # Process the image
        processed_image = await preprocess_image(
            image_source=file,
        )
        
        # Get dimensions
        height, width = processed_image.shape[:2]
        
        # Convert to base64 for response
        base64_image = image_to_base64(processed_image)
        
        return {
            "processed_image": base64_image,
            "width": width,
            "height": height,
        }
    
    async def process_base64_image(
        self,
        base64_string: str,
    ) -> Dict[str, Any]:

        # Simply use the preprocess_image function with appropriate parameters
        processed_image = await preprocess_image(
            image_source=base64_string
        )
        
        # Get dimensions
        height, width = processed_image.shape[:2]
        
        # Convert to base64 for response
        base64_image = image_to_base64(processed_image)
        
        return {
            "processed_image": base64_image,
            "width": width,
            "height": height,
            "processing_time_ms": 0.0  # Placeholder
        }

    async def optimize_for_mediapipe(
        self,
        image_source: Union[UploadFile, str, np.ndarray],
        high_resolution: bool = False
    ) -> Dict[str, Any]:
        # Use the preprocess_image function with MediaPipe-specific settings
        processed_image = await preprocess_image(
            image_source=image_source,
            high_resolution=high_resolution,
            apply_noise_filter=True
        )
        
        # Get dimensions
        height, width = processed_image.shape[:2]
        
        # Convert to base64 for response
        base64_image = image_to_base64(processed_image)
        
        return {
            "processed_image": base64_image,
            "width": width,
            "height": height,
            "high_resolution": high_resolution
        }

image_service = ImageService()
def get_image_service() -> ImageService:
    return image_service
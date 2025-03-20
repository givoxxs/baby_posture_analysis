import time
import numpy as np
from fastapi import UploadFile, HTTPException
from typing import Dict, Any, Tuple, Optional, Union

from app.utils.image_preprocessor import ImagePreProcessor

class ImageService:
    """Service for image processing operations"""
    
    def __init__(self, processor: Optional[ImagePreProcessor] = None):
        """
        Initialize the image service
        
        Args:
            processor: Optional ImagePreProcessor instance. If None, a default one is created.
        """
        self.processor = processor or ImagePreProcessor(width=640, height=480)
    
    async def validate_image_file(self, file: UploadFile) -> None:
        """
        Validate that the uploaded file is a valid image
        
        Args:
            file: UploadFile from FastAPI
            
        Raises:
            HTTPException: If file is not a valid image
        """
        content_type = file.content_type
        if not content_type or not content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, 
                detail=f"File must be an image, got {content_type}"
            )
    
    async def process_uploaded_image(
        self, 
        file: UploadFile, 
        apply_resize: bool = True,
        apply_normalize: bool = True, 
        apply_filter: bool = True,
        filter_type: str = "gaussian"
    ) -> Dict[str, Any]:
        """
        Process an uploaded image file with standard processing
        
        Args:
            file: UploadFile from FastAPI
            apply_resize: Whether to apply resizing
            apply_normalize: Whether to apply color normalization
            apply_filter: Whether to apply noise filtering
            filter_type: Type of noise filter to apply
            
        Returns:
            Dictionary with processed image and metadata
        """
        start_time = time.time()
        
        # Validate image
        await self.validate_image_file(file)
        
        # Process the image
        processed_image = await self.processor.preprocess_image(
            file,
            apply_resize=apply_resize,
            apply_normalize=apply_normalize,
            apply_filter=apply_filter,
            filter_type=filter_type
        )
        
        # Convert to base64 and prepare response
        return self._prepare_response(
            processed_image, 
            start_time,
            self.processor.width,
            self.processor.height,
            "Image processed successfully"
        )
    
    async def process_base64_image(
        self, 
        base64_str: str,
        apply_resize: bool = True,
        apply_normalize: bool = True, 
        apply_filter: bool = True,
        filter_type: str = "gaussian"
    ) -> Dict[str, Any]:
        """
        Process an image provided as base64 string
        
        Args:
            base64_str: Base64 encoded image string
            apply_resize: Whether to apply resizing
            apply_normalize: Whether to apply color normalization
            apply_filter: Whether to apply noise filtering
            filter_type: Type of noise filter to apply
            
        Returns:
            Dictionary with processed image and metadata
        """
        start_time = time.time()
        
        # Validate input
        if not base64_str:
            raise HTTPException(status_code=400, detail="Base64 image data is required")
        
        # Process the image
        processed_image = await self.processor.preprocess_image(
            base64_str,
            apply_resize=apply_resize,
            apply_normalize=apply_normalize,
            apply_filter=apply_filter,
            filter_type=filter_type
        )
        
        # Convert to base64 and prepare response
        return self._prepare_response(
            processed_image, 
            start_time,
            self.processor.width,
            self.processor.height,
            "Image processed successfully"
        )
    
    async def optimize_for_mediapipe(
        self, 
        file: UploadFile,
        high_resolution: bool = False
    ) -> Dict[str, Any]:
        """
        Process an image with optimizations for MediaPipe
        
        Args:
            file: UploadFile from FastAPI
            high_resolution: Whether to use higher resolution
            
        Returns:
            Dictionary with processed image and metadata
        """
        start_time = time.time()
        
        # Validate image
        await self.validate_image_file(file)
        
        # Process the image with MediaPipe optimizations
        processed_image = await self.processor.preprocess_for_mediapipe(
            file,
            high_resolution=high_resolution
        )
        
        # Get dimensions based on resolution setting
        width = 1280 if high_resolution else self.processor.width
        height = 720 if high_resolution else self.processor.height
        
        # Convert to base64 and prepare response
        return self._prepare_response(
            processed_image, 
            start_time,
            width,
            height,
            "Image processed for MediaPipe successfully"
        )
    
    def _prepare_response(
        self, 
        processed_image: np.ndarray,
        start_time: float,
        width: int,
        height: int,
        message: str = "Processing completed"
    ) -> Dict[str, Any]:
        """
        Prepare standardized response for processed images
        
        Args:
            processed_image: Processed image as numpy array
            start_time: Processing start time for timing calculation
            width: Width of the processed image
            height: Height of the processed image
            message: Success message
            
        Returns:
            Dictionary with standardized response format
        """
        # Convert processed image to base64
        base64_image = self.processor.to_base64(processed_image)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            "message": message,
            "processed_image": base64_image,
            "width": width,
            "height": height,
            "processing_time_ms": round(processing_time, 2)
        }

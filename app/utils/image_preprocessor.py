"""
Image preprocessing utilities.

This module provides a class for image preprocessing operations including
resizing, color normalization, and noise filtering.
"""
import base64
import cv2
import numpy as np
from typing import Tuple, Optional, Union, BinaryIO
from fastapi import UploadFile
import io
import logging

logger = logging.getLogger(__name__)

class ImagePreProcessor:
    """Class for preprocessing images to optimize for analysis."""
    
    def __init__(self, width: int = 640, height: int = 480):
        """
        Initialize the image preprocessor.
        
        Args:
            width: Default target width for resizing
            height: Default target height for resizing
        """
        self.width = width
        self.height = height
    
    async def preprocess_image(
        self,
        image_input: Union[str, bytes, UploadFile, np.ndarray],
        apply_resize: bool = True,
        apply_normalize: bool = True,
        apply_filter: bool = True,
        filter_type: str = "gaussian"
    ) -> np.ndarray:
        """
        Apply preprocessing pipeline to an image.
        
        Args:
            image_input: Input image as base64 string, bytes, UploadFile, or numpy array
            apply_resize: Whether to apply resizing
            apply_normalize: Whether to apply color normalization
            apply_filter: Whether to apply noise filtering
            filter_type: Type of noise filter to apply ("gaussian" or "median")
            
        Returns:
            Preprocessed image as numpy array
        """
        # Load the image
        image = await self._load_image(image_input)
        
        # Apply preprocessing steps
        if apply_resize:
            image = self.resize(image)
        
        if apply_normalize:
            image = self.normalize_colors(image)
            
        if apply_filter:
            image = self.reduce_noise(image, method=filter_type)
            
        return image
    
    async def preprocess_for_mediapipe(
        self,
        image_input: Union[str, bytes, UploadFile, np.ndarray],
        high_resolution: bool = False
    ) -> np.ndarray:
        """
        Apply preprocessing optimized for MediaPipe.
        
        Args:
            image_input: Input image as base64 string, bytes, UploadFile, or numpy array
            high_resolution: Whether to use high resolution (1280x720)
            
        Returns:
            Preprocessed image as numpy array
        """
        # Load the image
        image = await self._load_image(image_input)
        
        # MediaPipe works better with RGB
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Check if already RGB (this is a heuristic)
            if np.mean(image[:, :, 0]) < np.mean(image[:, :, 2]):
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize based on resolution setting
        if high_resolution:
            image = self.resize(image, target_size=(1280, 720))
        else:
            image = self.resize(image)
            
        # Apply mild noise reduction
        image = self.reduce_noise(image, method="gaussian", kernel_size=3)
        
        return image
    
    async def _load_image(
        self, 
        image_input: Union[str, bytes, UploadFile, np.ndarray]
    ) -> np.ndarray:
        """
        Load an image from various input types.
        
        Args:
            image_input: Input image as base64 string, bytes, UploadFile, or numpy array
            
        Returns:
            Image as numpy array
            
        Raises:
            ValueError: If image cannot be loaded
        """
        if isinstance(image_input, np.ndarray):
            return image_input
            
        elif isinstance(image_input, UploadFile):
            contents = await image_input.read()
            nparr = np.frombuffer(contents, np.uint8)
            
        elif isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            
        elif isinstance(image_input, str):
            # Assuming base64 string
            if image_input.startswith('data:image'):
                # Remove header if present
                image_input = image_input.split(',')[1]
                
            try:
                imgdata = base64.b64decode(image_input)
                nparr = np.frombuffer(imgdata, np.uint8)
            except Exception as e:
                logger.error(f"Failed to decode base64 string: {e}")
                raise ValueError("Invalid base64 image data")
        else:
            raise ValueError("Unsupported image input type")
            
        # Decode the image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image")
            
        return img
    
    def resize(
        self, 
        image: np.ndarray, 
        target_size: Optional[Tuple[int, int]] = None
    ) -> np.ndarray:
        """
        Resize an image to the target size.
        
        Args:
            image: Input image as numpy array
            target_size: Target dimensions as (width, height)
            
        Returns:
            Resized image
        """
        if target_size is None:
            target_size = (self.width, self.height)
            
        # Skip if already at target size
        if image.shape[1] == target_size[0] and image.shape[0] == target_size[1]:
            return image
        
        return cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)
    
    def normalize_colors(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize image colors, adjusting brightness and contrast.
        
        Args:
            image: Input image
            
        Returns:
            Normalized image
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Split channels
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        
        # Merge channels
        merged = cv2.merge([cl, a, b])
        
        # Convert back to BGR
        normalized = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        
        return normalized
    
    def reduce_noise(
        self, 
        image: np.ndarray, 
        method: str = "gaussian",
        kernel_size: int = 5
    ) -> np.ndarray:
        """
        Apply noise reduction filter to an image.
        
        Args:
            image: Input image
            method: Filtering method ('gaussian' or 'median')
            kernel_size: Size of the kernel for filtering
            
        Returns:
            Filtered image with reduced noise
        """
        # Ensure kernel size is odd
        if kernel_size % 2 == 0:
            kernel_size += 1
            
        if method == "gaussian":
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        elif method == "median":
            return cv2.medianBlur(image, kernel_size)
        else:
            logger.warning(f"Unknown noise reduction method: {method}, using gaussian")
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    
    def to_base64(self, image: np.ndarray, format: str = ".jpg") -> str:
        """
        Convert an image to base64 string.
        
        Args:
            image: Input image as numpy array
            format: Image format ('.jpg', '.png', etc.)
            
        Returns:
            Base64 encoded image string
        """
        success, buffer = cv2.imencode(format, image)
        if not success:
            logger.error("Failed to encode image")
            return ""
            
        encoded = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/{format[1:]};base64,{encoded}"
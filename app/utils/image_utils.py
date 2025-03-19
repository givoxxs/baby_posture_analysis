import cv2
import numpy as np
import base64
from typing import List, Tuple, Union, Optional
from PIL import Image
from io import BytesIO
from fastapi import UploadFile

class ImagePreProcessor: 
    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        
    async def load_image_from_upload(self, file: UploadFile) -> np.ndarray:
        """
        Load image from FastAPI UploadFile
        
        Args:
            file: UploadFile from FastAPI
            
        Returns:
            numpy array of the image
        """
        content = await file.read()
        img = np.asarray(bytearray(content), dtype="uint8")
        img = cv2.imdecode(img, cv2.IMREAD_COLOR) # Convert to BGR format
        return img

    def load_image_from_base64(self, base64_str: str) -> np.ndarray:
        """
        Load image from base64 string
        
        Args:
            base64_str: Base64 encoded image string
            
        Returns:
            numpy array of the image
        """
        # Handle potential data URI prefix
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
            
        img_data = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    
    def resize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Resize image to standard dimensions
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Resized image
        """
        return cv2.resize(image, (self.width, self.height), interpolation=cv2.INTER_AREA) 
    
    def normalize_colors(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize colors, convert to RGB if needed, and adjust brightness/contrast
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Color normalized image
        """
        # Convert BGR to RGB if needed
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
        # Apply histogram equalization for contrast enhancement
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        lab = cv2.merge((l, a, b))
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        
        # Normalize pixel values
        enhanced = enhanced.astype("float32") / 255.0
        
        return enhanced
    
    def filter_noise(self, image: np.ndarray, filter_type: str = 'gaussian', kernel_size: int = 5) -> np.ndarray:
        """
        Apply noise filtering
        
        Args:
            image: Input image as numpy array
            filter_type: Type of filter ('gaussian' or 'median')
            kernel_size: Size of the kernel
            
        Returns:
            Filtered image
        """
        if filter_type.lower() == 'gaussian':
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        elif filter_type.lower() == 'median':
            return cv2.medianBlur(image, kernel_size)
        else:
            return image
    
    async def preprocess_image(self, 
                              image_source: Union[UploadFile, str, np.ndarray],
                              apply_resize: bool = True,
                              apply_normalize: bool = True, 
                              apply_filter: bool = True,
                              filter_type: str = 'gaussian') -> np.ndarray:
        """
        Complete preprocessing pipeline for images
        
        Args:
            image_source: UploadFile, base64 string or numpy array
            apply_resize: Whether to apply resizing
            apply_normalize: Whether to apply color normalization
            apply_filter: Whether to apply noise filtering
            filter_type: Type of noise filter to apply
            
        Returns:
            Preprocessed image
        """
        # Load image based on source type
        if isinstance(image_source, UploadFile):
            image = await self.load_image_from_upload(image_source)
        elif isinstance(image_source, str):
            image = self.load_image_from_base64(image_source)
        elif isinstance(image_source, np.ndarray):
            image = image_source
        else:
            raise ValueError("Unsupported image source type")
            
        # Apply preprocessing steps
        if apply_resize:
            image = self.resize_image(image)
            
        if apply_filter:
            image = self.filter_noise(image, filter_type)
            
        if apply_normalize:
            image = self.normalize_colors(image)
            
        return image
    
    def to_base64(self, image: np.ndarray) -> str:
        """
        Convert processed image to base64 for easy transmission
        
        Args:
            image: Processed image as numpy array
            
        Returns:
            Base64 encoded string
        """
        # If image is normalized to float values, convert back to uint8
        if image.dtype == np.float32 or image.dtype == np.float64:
            image = (image * 255).astype(np.uint8)
            
        # Convert to RGB if not already
        if len(image.shape) == 3 and image.shape[2] == 3:
            if image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Encode as JPEG
        success, buffer = cv2.imencode('.jpg', image)
        if not success:
            raise ValueError("Failed to encode image")
            
        # Convert to base64
        base64_str = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{base64_str}"

    def enhance_for_pose_detection(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image specifically for MediaPipe pose detection
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Enhanced image optimized for pose detection
        """
        # Make sure image is in RGB format
        if len(image.shape) == 3 and image.shape[2] == 3:
            if image.dtype == np.float32 or image.dtype == np.float64:
                image = (image * 255).astype(np.uint8)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
        # Enhance edges to help with keypoint detection
        sharpening_kernel = np.array([[-1, -1, -1], 
                                      [-1, 9, -1], 
                                      [-1, -1, -1]])
        sharpened = cv2.filter2D(image, -1, sharpening_kernel)
        
        # Ensure good lighting by applying adaptive equalization
        lab = cv2.cvtColor(sharpened, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge((l, a, b))
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        
        # Optional: Apply slight Gaussian blur to reduce artifacts from sharpening (kernel size 3)
        enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)
        
        return enhanced

    async def preprocess_for_mediapipe(self, 
                                      image_source: Union[UploadFile, str, np.ndarray],
                                      high_resolution: bool = False) -> np.ndarray:
        """
        Specialized preprocessing pipeline optimized for MediaPipe
        
        Args:
            image_source: UploadFile, base64 string or numpy array
            high_resolution: Whether to use higher resolution (720p) for better keypoint detection
            
        Returns:
            Preprocessed image optimized for MediaPipe
        """
        # Load image based on source type
        if isinstance(image_source, UploadFile):
            image = await self.load_image_from_upload(image_source)
        elif isinstance(image_source, str):
            image = self.load_image_from_base64(image_source)
        elif isinstance(image_source, np.ndarray):
            image = image_source
        else:
            raise ValueError("Unsupported image source type")
        
        # Resize to appropriate resolution
        if high_resolution:
            # Higher resolution for more accurate keypoints
            image = cv2.resize(image, (1280, 720), interpolation=cv2.INTER_AREA)
        else:
            image = self.resize_image(image)
        
        # Apply median blur (better preserves edges than Gaussian for pose detection)
        image = self.filter_noise(image, filter_type='median', kernel_size=3)
        
        # Apply enhanced processing specifically for pose detection
        image = self.enhance_for_pose_detection(image)
        
        return image


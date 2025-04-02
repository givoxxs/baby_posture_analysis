"""
Utility functions for image processing.
"""

import cv2
import numpy as np
import base64
from fastapi import UploadFile
from typing import Union, Tuple
import io
from PIL import Image


async def load_image(file: UploadFile) -> np.ndarray:
    """Load image from an uploaded file."""
    try: 
        await file.seek(0)
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
        if image is None:
            raise ValueError(f"Failed to decode image from {file.filename}")
    except Exception as e:
        raise ValueError(f"Error loading image: {str(e)}")
    return image


def load_image_from_base64(base64_string: str) -> np.ndarray:
    """Load image from a base64 string."""
    if "," in base64_string:
        base64_string = base64_string.split(",", 1)[1]
        
    img_data = base64.b64decode(base64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Failed to decode base64 image")
        
    return image


def resize_image(image: np.ndarray, width: int = 640, height: int = 480) -> np.ndarray:
    """Resize image to specified dimensions."""
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)


def normalize_colors(image: np.ndarray) -> np.ndarray:
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


def filter_noise(image: np.ndarray, filter_type: str = "gaussian", kernel_size: int = 5) -> np.ndarray:
    """Apply noise filtering to image."""
    if filter_type.lower() == "gaussian":
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    elif filter_type.lower() == "median":
        return cv2.medianBlur(image, kernel_size)
    else:
        return image  # No filtering if unknown type


def enhance_for_pose_detection(image: np.ndarray) -> np.ndarray:
    # Convert to uint8 if needed
    if image.dtype != np.uint8:
        image = (image * 255).astype(np.uint8)
        
    # Convert to RGB if in BGR format
    if len(image.shape) == 3 and image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
    # Enhance edges
    sharpening_kernel = np.array([[-1, -1, -1], 
                                [-1, 9, -1], 
                                [-1, -1, -1]])
    sharpened = cv2.filter2D(image, -1, sharpening_kernel)
    
    # Convert to LAB color space
    lab = cv2.cvtColor(sharpened, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    
    # Ensure L channel is in uint8 format before applying CLAHE
    if l.dtype != np.uint8:
        l = (l * 255).astype(np.uint8)
        
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    
    # Merge channels back
    lab = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    
    # Apply slight Gaussian blur
    enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)
    
    return enhanced


def to_base64(self, image: np.ndarray) -> str:
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

def save_image(image: np.ndarray, filepath: str) -> bool:
    """Save image to file."""
    return cv2.imwrite(filepath, image)

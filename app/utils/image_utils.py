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
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError(f"Failed to decode image from {file.filename}")
        
    return image


def load_image_from_base64(base64_string: str) -> np.ndarray:
    """Load image from a base64 string."""
    # Remove data URL prefix if present
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
    """Normalize image colors for better processing."""
    # Convert to RGB if needed
    if len(image.shape) == 3:
        # Apply histogram equalization in LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        enhanced_lab = cv2.merge((cl, a, b))
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    else:
        # Apply standard histogram equalization for grayscale
        return cv2.equalizeHist(image)


def filter_noise(image: np.ndarray, filter_type: str = "gaussian", kernel_size: int = 5) -> np.ndarray:
    """Apply noise filtering to image."""
    if filter_type.lower() == "gaussian":
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    elif filter_type.lower() == "median":
        return cv2.medianBlur(image, kernel_size)
    else:
        return image  # No filtering if unknown type


def enhance_for_pose_detection(image: np.ndarray) -> np.ndarray:
    """Enhance image for better pose detection."""
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    
    # Split into channels
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    
    # Merge back the channels
    enhanced_lab = cv2.merge((cl, a, b))
    
    # Convert back to BGR
    enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    
    # Slightly increase contrast
    alpha = 1.2  # Contrast control (1.0-3.0)
    beta = 10    # Brightness control (0-100)
    adjusted = cv2.convertScaleAbs(enhanced_bgr, alpha=alpha, beta=beta)
    
    return adjusted


def to_base64(image: np.ndarray) -> str:
    """Convert image to base64 string."""
    success, buffer = cv2.imencode('.png', image)
    if not success:
        raise ValueError("Failed to encode image to PNG format")
    
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/png;base64,{encoded_image}"


def save_image(image: np.ndarray, filepath: str) -> bool:
    """Save image to file."""
    return cv2.imwrite(filepath, image)

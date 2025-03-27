"""
Image preprocessing utilities for baby posture analysis.

This module provides functions for preprocessing images before pose detection,
including resizing, color normalization, and noise filtering.
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def resize_image(image: np.ndarray, target_size: Tuple[int, int] = (640, 480)) -> np.ndarray:
    """
    Resize an image to the target size.
    
    Args:
        image: Input image as numpy array
        target_size: Target dimensions as (width, height)
        
    Returns:
        Resized image
    """
    if image.shape[1] == target_size[0] and image.shape[0] == target_size[1]:
        return image
    
    return cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)

def normalize_colors(image: np.ndarray) -> np.ndarray:
    """
    Normalize image colors, adjusting brightness and contrast.
    
    Args:
        image: Input RGB image
        
    Returns:
        Normalized image
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    
    # Normalize L channel
    l, a, b = cv2.split(lab)
    l_mean, l_std = l.mean(), l.std()
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    
    # Merge channels
    merged = cv2.merge([cl, a, b])
    
    # Convert back to RGB
    normalized = cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)
    
    return normalized

def reduce_noise(image: np.ndarray, method: str = 'gaussian', kernel_size: int = 5) -> np.ndarray:
    """
    Apply noise reduction filter to an image.
    
    Args:
        image: Input image
        method: Filtering method ('gaussian' or 'median')
        kernel_size: Size of the kernel for filtering
        
    Returns:
        Filtered image with reduced noise
    """
    if method == 'gaussian':
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    elif method == 'median':
        return cv2.medianBlur(image, kernel_size)
    else:
        logger.warning(f"Unknown noise reduction method: {method}, using gaussian as default")
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)

def preprocess_image(
    image: np.ndarray, 
    target_size: Tuple[int, int] = (640, 480),
    normalize: bool = True,
    denoise: bool = True,
    denoise_method: str = 'gaussian'
) -> np.ndarray:
    """
    Apply full preprocessing pipeline to an image.
    
    Args:
        image: Input image
        target_size: Target dimensions as (width, height)
        normalize: Whether to apply color normalization
        denoise: Whether to apply noise reduction
        denoise_method: Method for noise reduction ('gaussian' or 'median')
        
    Returns:
        Preprocessed image
    """
    # Resize image
    processed = resize_image(image, target_size)
    
    # Apply color normalization if requested
    if normalize:
        processed = normalize_colors(processed)
    
    # Apply noise reduction if requested
    if denoise:
        processed = reduce_noise(processed, method=denoise_method)
    
    return processed

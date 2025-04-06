import numpy as np
import cv2
from fastapi import UploadFile
import base64
from io import BytesIO
from typing import Union, Tuple

async def load_image(file: UploadFile) -> np.ndarray:
    """Load image from UploadFile object"""
    print("Loading image from UploadFile")
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return image

def load_image_from_base64(base64_str: str) -> np.ndarray:
    """Load image from base64 string"""
    if ',' in base64_str:
        # Remove data URL prefix if present
        base64_str = base64_str.split(',')[1]
    image_data = base64.b64decode(base64_str)
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return image

def resize_image(image: np.ndarray, width: int = 640, height: int = 480) -> np.ndarray:
    """Resize image to specified dimensions"""
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

def normalize_colors(image: np.ndarray) -> np.ndarray:
    """Normalize colors and enhance image contrast"""
    # Convert BGR to RGB if needed
    if image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Apply histogram equalization for contrast enhancement
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

def filter_noise(image: np.ndarray, filter_type: str = 'gaussian', kernel_size: int = 3) -> np.ndarray:
    """Apply noise filtering to image"""
    if filter_type == 'gaussian':
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    elif filter_type == 'median':
        return cv2.medianBlur(image, kernel_size)
    else:
        return image

def enhance_for_pose_detection(image: np.ndarray) -> np.ndarray:
    """Enhance image specifically for pose detection"""
    # Convert to uint8 if needed
    if image.dtype != np.uint8:
        image = (image * 255).astype(np.uint8)
    
    # Convert to RGB if in BGR format
    if len(image.shape) == 3 and image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Enhance edges
    sharpening_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(image, -1, sharpening_kernel)
    
    # Apply CLAHE to enhance contrast
    lab = cv2.cvtColor(sharpened, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    
    # Ensure L channel is in uint8 format
    if l.dtype != np.uint8:
        l = (l * 255).astype(np.uint8)
    
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    
    lab = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    
    # Apply slight Gaussian blur
    enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)
    
    return enhanced

def image_to_base64(image: np.ndarray) -> str:
    """Convert image to base64 string"""
    success, buffer = cv2.imencode('.jpg', image)
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{encoded_image}"

async def preprocess_image(
    image_source: Union[UploadFile, str, np.ndarray]
) -> np.ndarray:
    # Load image based on source type
    if hasattr(image_source, "read") and callable(getattr(image_source, "read")):
        image = await load_image(image_source)
    elif isinstance(image_source, str):
        image = load_image_from_base64(image_source)
    elif isinstance(image_source, np.ndarray):
        image = image_source
    else:
        raise ValueError(f"Unsupported image source type: {type(image_source)}")
    
    print("image shape:", image.shape)
    if image.shape[0] > image.shape[1]:
        print("width > height")
        image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        print(image.shape[0], image.shape[1])
    
    image = resize_image(image, width=640, height=480)

    image = filter_noise(image, filter_type='median', kernel_size=3)

    image = normalize_colors(image)
    
    image = enhance_for_pose_detection(image)
    
    return image

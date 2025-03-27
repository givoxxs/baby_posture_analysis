"""Module for detecting blanket kicking behavior from keypoints."""

import numpy as np
from typing import Dict, Any, Tuple
from .constants import *

def define_blanket_region(keypoints: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Define the blanket region based on body position.
    
    Args:
        keypoints: Array of keypoints
        
    Returns:
        Tuple of (top_left, bottom_right) coordinates of blanket region
    """
    # Default blanket region
    top_left = np.array([-1.0, -1.0, -1.0])
    bottom_right = np.array([1.0, 1.0, 1.0])
    
    # Get head position (using nose or the average of eyes if nose not available)
    head_pos = None
    if NOSE < len(keypoints):
        head_pos = keypoints[NOSE][:3]
    elif LEFT_EYE < len(keypoints) and RIGHT_EYE < len(keypoints):
        head_pos = (keypoints[LEFT_EYE][:3] + keypoints[RIGHT_EYE][:3]) / 2
    
    # Get hip position (average of left and right hip)
    hip_pos = None
    if LEFT_HIP < len(keypoints) and RIGHT_HIP < len(keypoints):
        hip_pos = (keypoints[LEFT_HIP][:3] + keypoints[RIGHT_HIP][:3]) / 2
    
    # If we have both head and hip positions, define blanket region
    if head_pos is not None and hip_pos is not None:
        # Determine body orientation (assuming Y is height)
        body_direction = hip_pos - head_pos
        body_length = np.linalg.norm(body_direction)
        
        # Blanket should cover from hips to below feet
        blanket_top = hip_pos
        
        # Extend blanket to 1.5x the body length in the body direction
        blanket_bottom = hip_pos + 1.5 * body_length * (body_direction / body_length)
        
        # Add width to the blanket (perpendicular to body direction)
        if (LEFT_HIP < len(keypoints) and RIGHT_HIP < len(keypoints)):
            hip_width = np.linalg.norm(keypoints[LEFT_HIP][:3] - keypoints[RIGHT_HIP][:3])
            
            # Create a perpendicular vector to the body direction in the horizontal plane
            if np.abs(body_direction[0]) > 1e-6 or np.abs(body_direction[2]) > 1e-6:
                perp_direction = np.array([-body_direction[2], 0, body_direction[0]])
                perp_direction = perp_direction / np.linalg.norm(perp_direction)
                
                # Extend blanket width to 2x hip width on each side
                blanket_left = blanket_top - 2 * hip_width * perp_direction
                blanket_right = blanket_top + 2 * hip_width * perp_direction
                
                # Update region bounds
                top_left = np.minimum(blanket_left, blanket_bottom)
                bottom_right = np.maximum(blanket_right, blanket_top)
            else:
                # If body is perfectly vertical, use X-Z plane for width
                top_left = np.array([hip_pos[0] - 2*hip_width, blanket_top[1], hip_pos[2] - 2*hip_width])
                bottom_right = np.array([hip_pos[0] + 2*hip_width, blanket_bottom[1], hip_pos[2] + 2*hip_width])
    
    return top_left, bottom_right

def detect_blanket_kick(keypoints: np.ndarray) -> Dict[str, Any]:
    """
    Detect if the baby is kicking off blanket.
    
    Args:
        keypoints: Array of keypoints
        
    Returns:
        Dictionary with blanket kick features
    """
    blanket_features = {
        'blanket_kicked': False,
        'kick_confidence': 0.0,
        'feet_outside_blanket': False,
        'feet_movement': 0.0
    }
    
    # Define blanket region
    blanket_top_left, blanket_bottom_right = define_blanket_region(keypoints)
    
    # Check if ankles/feet are outside the blanket region
    for ankle_idx in [LEFT_ANKLE, RIGHT_ANKLE]:
        if ankle_idx < len(keypoints):
            ankle_pos = keypoints[ankle_idx][:3]
            
            # Check if ankle is outside the defined blanket region
            outside_x = ankle_pos[0] < blanket_top_left[0] or ankle_pos[0] > blanket_bottom_right[0]
            outside_y = ankle_pos[1] < blanket_top_left[1] or ankle_pos[1] > blanket_bottom_right[1]
            outside_z = ankle_pos[2] < blanket_top_left[2] or ankle_pos[2] > blanket_bottom_right[2]
            
            if outside_x or outside_y or outside_z:
                blanket_features['feet_outside_blanket'] = True
                blanket_features['blanket_kicked'] = True
                
                # Calculate how far outside the foot is (relative to blanket size)
                blanket_size = blanket_bottom_right - blanket_top_left
                blanket_size = np.maximum(blanket_size, 1e-6)  # Avoid division by zero
                
                outside_distance = [
                    max(0, blanket_top_left[0] - ankle_pos[0], ankle_pos[0] - blanket_bottom_right[0]) / blanket_size[0],
                    max(0, blanket_top_left[1] - ankle_pos[1], ankle_pos[1] - blanket_bottom_right[1]) / blanket_size[1],
                    max(0, blanket_top_left[2] - ankle_pos[2], ankle_pos[2] - blanket_bottom_right[2]) / blanket_size[2]
                ]
                
                outside_ratio = np.mean([d for d in outside_distance if not np.isnan(d)])
                blanket_features['kick_confidence'] = max(blanket_features['kick_confidence'], outside_ratio)
    
    return blanket_features

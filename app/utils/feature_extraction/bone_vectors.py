"""Module for extracting and normalizing bone vectors from keypoints."""

import numpy as np
from typing import Dict, List, Tuple, Any
from .constants import BONE_PAIRS

def extract_bone_vectors(keypoints: np.ndarray) -> Dict[Tuple[int, int], np.ndarray]:
    """
    Extract bone vectors from keypoints.
    
    Args:
        keypoints: Array of shape (N, 3) or (N, 4) where N is the number of keypoints,
                  and each row contains [x, y, z, (visibility)]
    
    Returns:
        Dictionary mapping bone pairs to their corresponding vectors
    """
    bone_vectors = {}
    
    for start_idx, end_idx in BONE_PAIRS:
        # Check if both keypoints are detected
        if start_idx < len(keypoints) and end_idx < len(keypoints):
            start_point = keypoints[start_idx][:3]  # Take x, y, z
            end_point = keypoints[end_idx][:3]      # Take x, y, z
            
            # Calculate the bone vector
            vector = end_point - start_point
            
            # Store the vector
            bone_vectors[(start_idx, end_idx)] = vector
    
    return bone_vectors

def normalize_bone_vectors(bone_vectors: Dict[Tuple[int, int], np.ndarray]) -> Dict[Tuple[int, int], np.ndarray]:
    """
    Normalize bone vectors to unit length for scale invariance.
    
    Args:
        bone_vectors: Dictionary mapping bone pairs to their vectors
        
    Returns:
        Dictionary mapping bone pairs to their normalized vectors
    """
    normalized_vectors = {}
    
    for bone_pair, vector in bone_vectors.items():
        # Calculate vector magnitude
        magnitude = np.linalg.norm(vector)
        
        # Avoid division by zero
        if magnitude > 1e-6:
            normalized_vectors[bone_pair] = vector / magnitude
        else:
            normalized_vectors[bone_pair] = vector
    
    return normalized_vectors

def get_reference_scale(bone_vectors: Dict[Tuple[int, int], np.ndarray]) -> float:
    """
    Calculate a reference scale based on torso size for normalization.
    
    Args:
        bone_vectors: Dictionary mapping bone pairs to their vectors
        
    Returns:
        Reference scale (e.g., torso length)
    """
    from .constants import LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP
    
    # Try to use shoulder width as reference
    if (LEFT_SHOULDER, RIGHT_SHOULDER) in bone_vectors:
        return np.linalg.norm(bone_vectors[(LEFT_SHOULDER, RIGHT_SHOULDER)])
    
    # Fallback to hip width
    if (LEFT_HIP, RIGHT_HIP) in bone_vectors:
        return np.linalg.norm(bone_vectors[(LEFT_HIP, RIGHT_HIP)])
    
    # Default value if nothing works
    return 1.0

"""Module for computing distance-based features from keypoints."""

import numpy as np
from typing import Dict, List, Tuple, Any
from .constants import *
from .bone_vectors import get_reference_scale

def compute_distance_features(keypoints: np.ndarray, 
                              bone_vectors: Dict[Tuple[int, int], np.ndarray]) -> Dict[str, float]:
    """
    Compute distance-based features from keypoints.
    
    Args:
        keypoints: Array of keypoints
        bone_vectors: Dictionary of bone vectors
        
    Returns:
        Dictionary of distance features
    """
    distance_features = {}
    
    # Get reference scale for normalization
    reference_scale = get_reference_scale(bone_vectors)
    
    # Distance between shoulders (normalized)
    if LEFT_SHOULDER < len(keypoints) and RIGHT_SHOULDER < len(keypoints):
        left_shoulder = keypoints[LEFT_SHOULDER][:3]
        right_shoulder = keypoints[RIGHT_SHOULDER][:3]
        shoulder_distance = np.linalg.norm(right_shoulder - left_shoulder)
        distance_features['shoulder_width'] = shoulder_distance / reference_scale
    
    # Nose to bed plane distance (for face-down detection)
    # Assuming bed is on XZ plane (Y is height)
    if NOSE < len(keypoints):
        nose_y = keypoints[NOSE][1]  # Y coordinate
        
        # Estimate bed plane from ankle positions if available
        bed_y = 0
        ankle_count = 0
        if LEFT_ANKLE < len(keypoints) and keypoints[LEFT_ANKLE][1] > 0:
            bed_y += keypoints[LEFT_ANKLE][1]
            ankle_count += 1
        if RIGHT_ANKLE < len(keypoints) and keypoints[RIGHT_ANKLE][1] > 0:
            bed_y += keypoints[RIGHT_ANKLE][1]
            ankle_count += 1
            
        if ankle_count > 0:
            bed_y /= ankle_count
            distance_features['nose_to_bed_distance'] = (nose_y - bed_y) / reference_scale
    
    # Hand to face distances (for face occlusion detection)
    if NOSE < len(keypoints):
        nose_pos = keypoints[NOSE][:3]
        
        if LEFT_WRIST < len(keypoints):
            left_wrist_pos = keypoints[LEFT_WRIST][:3]
            left_hand_face_dist = np.linalg.norm(nose_pos - left_wrist_pos)
            distance_features['left_hand_face_distance'] = left_hand_face_dist / reference_scale
            
        if RIGHT_WRIST < len(keypoints):
            right_wrist_pos = keypoints[RIGHT_WRIST][:3]
            right_hand_face_dist = np.linalg.norm(nose_pos - right_wrist_pos)
            distance_features['right_hand_face_distance'] = right_hand_face_dist / reference_scale
    
    # Hands to torso distances (for bent arms)
    if LEFT_SHOULDER < len(keypoints) and RIGHT_SHOULDER < len(keypoints) and LEFT_HIP < len(keypoints) and RIGHT_HIP < len(keypoints):
        # Calculate torso center
        torso_center = (keypoints[LEFT_SHOULDER][:3] + keypoints[RIGHT_SHOULDER][:3] + 
                         keypoints[LEFT_HIP][:3] + keypoints[RIGHT_HIP][:3]) / 4
        
        if LEFT_WRIST < len(keypoints):
            left_wrist_pos = keypoints[LEFT_WRIST][:3]
            distance_features['left_hand_torso_distance'] = np.linalg.norm(left_wrist_pos - torso_center) / reference_scale
            
        if RIGHT_WRIST < len(keypoints):
            right_wrist_pos = keypoints[RIGHT_WRIST][:3]
            distance_features['right_hand_torso_distance'] = np.linalg.norm(right_wrist_pos - torso_center) / reference_scale
    
    # Feet to torso distances (for bent legs)
    if LEFT_HIP < len(keypoints) and RIGHT_HIP < len(keypoints):
        # Calculate hip center
        hip_center = (keypoints[LEFT_HIP][:3] + keypoints[RIGHT_HIP][:3]) / 2
        
        if LEFT_ANKLE < len(keypoints):
            left_ankle_pos = keypoints[LEFT_ANKLE][:3]
            distance_features['left_foot_hip_distance'] = np.linalg.norm(left_ankle_pos - hip_center) / reference_scale
            
        if RIGHT_ANKLE < len(keypoints):
            right_ankle_pos = keypoints[RIGHT_ANKLE][:3]
            distance_features['right_foot_hip_distance'] = np.linalg.norm(right_ankle_pos - hip_center) / reference_scale
    
    return distance_features

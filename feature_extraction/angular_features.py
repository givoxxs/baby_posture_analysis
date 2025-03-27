"""Module for computing angular features from bone vectors."""

import numpy as np
from typing import Dict, List, Tuple, Any
from .constants import *

def angle_between_vectors(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate the angle between two vectors in degrees.
    
    Args:
        v1: First vector
        v2: Second vector
        
    Returns:
        Angle in degrees
    """
    # Normalize vectors
    v1_norm = v1 / np.linalg.norm(v1)
    v2_norm = v2 / np.linalg.norm(v2)
    
    # Calculate dot product
    dot_product = np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0)
    
    # Calculate angle in degrees
    angle_rad = np.arccos(dot_product)
    angle_deg = np.degrees(angle_rad)
    
    return angle_deg

def compute_angular_features(keypoints: np.ndarray, bone_vectors: Dict[Tuple[int, int], np.ndarray]) -> Dict[str, float]:
    """
    Compute angular features from keypoints and bone vectors.
    
    Args:
        keypoints: Array of keypoints
        bone_vectors: Dictionary of bone vectors
        
    Returns:
        Dictionary of angular features
    """
    angular_features = {}
    
    # Vertical reference vector (pointing upward in 3D space)
    vertical_vector = np.array([0, 1, 0])
    
    # Horizontal reference vector
    horizontal_vector = np.array([1, 0, 0])
    
    # Head-body angle (angle between vertical and nose-to-mid-shoulders)
    if NOSE < len(keypoints) and LEFT_SHOULDER < len(keypoints) and RIGHT_SHOULDER < len(keypoints):
        mid_shoulder = (keypoints[LEFT_SHOULDER][:3] + keypoints[RIGHT_SHOULDER][:3]) / 2
        head_vector = keypoints[NOSE][:3] - mid_shoulder
        if np.linalg.norm(head_vector) > 1e-6:
            angular_features['head_body_angle'] = angle_between_vectors(head_vector, vertical_vector)
    
    # Arm bend angles
    if (LEFT_SHOULDER, LEFT_ELBOW) in bone_vectors and (LEFT_ELBOW, LEFT_WRIST) in bone_vectors:
        upper_arm_vec = bone_vectors[(LEFT_SHOULDER, LEFT_ELBOW)]
        forearm_vec = bone_vectors[(LEFT_ELBOW, LEFT_WRIST)]
        angular_features['left_arm_bend'] = angle_between_vectors(upper_arm_vec, forearm_vec)
    
    if (RIGHT_SHOULDER, RIGHT_ELBOW) in bone_vectors and (RIGHT_ELBOW, RIGHT_WRIST) in bone_vectors:
        upper_arm_vec = bone_vectors[(RIGHT_SHOULDER, RIGHT_ELBOW)]
        forearm_vec = bone_vectors[(RIGHT_ELBOW, RIGHT_WRIST)]
        angular_features['right_arm_bend'] = angle_between_vectors(upper_arm_vec, forearm_vec)
    
    # Leg bend angles
    if (LEFT_HIP, LEFT_KNEE) in bone_vectors and (LEFT_KNEE, LEFT_ANKLE) in bone_vectors:
        thigh_vec = bone_vectors[(LEFT_HIP, LEFT_KNEE)]
        calf_vec = bone_vectors[(LEFT_KNEE, LEFT_ANKLE)]
        angular_features['left_leg_bend'] = angle_between_vectors(thigh_vec, calf_vec)
    
    if (RIGHT_HIP, RIGHT_KNEE) in bone_vectors and (RIGHT_KNEE, RIGHT_ANKLE) in bone_vectors:
        thigh_vec = bone_vectors[(RIGHT_HIP, RIGHT_KNEE)]
        calf_vec = bone_vectors[(RIGHT_KNEE, RIGHT_ANKLE)]
        angular_features['right_leg_bend'] = angle_between_vectors(thigh_vec, calf_vec)
    
    # Body tilt angle
    if (LEFT_SHOULDER, LEFT_HIP) in bone_vectors:
        torso_vec = bone_vectors[(LEFT_SHOULDER, LEFT_HIP)]
        angular_features['left_body_tilt'] = angle_between_vectors(torso_vec, vertical_vector)
    
    if (RIGHT_SHOULDER, RIGHT_HIP) in bone_vectors:
        torso_vec = bone_vectors[(RIGHT_SHOULDER, RIGHT_HIP)]
        angular_features['right_body_tilt'] = angle_between_vectors(torso_vec, vertical_vector)
    
    # Shoulders angle with horizontal
    if (LEFT_SHOULDER, RIGHT_SHOULDER) in bone_vectors:
        shoulder_vec = bone_vectors[(LEFT_SHOULDER, RIGHT_SHOULDER)]
        angular_features['shoulder_horizontal_angle'] = angle_between_vectors(shoulder_vec, horizontal_vector)
    
    return angular_features

"""Module for detecting face occlusion using keypoints."""

import numpy as np
from typing import Dict, Any
from .constants import FACE_KEYPOINTS, HAND_KEYPOINTS, NOSE, LEFT_EYE, RIGHT_EYE, LEFT_EAR, RIGHT_EAR, LEFT_WRIST, RIGHT_WRIST

def detect_face_occlusion(keypoints: np.ndarray) -> Dict[str, Any]:
    """
    Detect if the face is occluded by hands or other objects.
    
    Args:
        keypoints: Array of keypoints with shape (N, 4), where the last dimension is [x, y, z, visibility]
        
    Returns:
        Dictionary with face occlusion features
    """
    occlusion_features = {
        'face_occluded': False,
        'occlusion_confidence': 0.0,
        'visible_face_keypoints_ratio': 1.0,
        'hand_near_face': False
    }
    
    # Check face keypoint visibility
    visible_face_keypoints = 0
    total_face_keypoints = len(FACE_KEYPOINTS)
    
    face_visibility_threshold = 0.5  # Minimum visibility score to consider a keypoint visible
    
    for idx in FACE_KEYPOINTS:
        if idx < len(keypoints) and len(keypoints[idx]) >= 4:
            visibility = keypoints[idx][3]
            if visibility > face_visibility_threshold:
                visible_face_keypoints += 1
    
    if total_face_keypoints > 0:
        visible_ratio = visible_face_keypoints / total_face_keypoints
        occlusion_features['visible_face_keypoints_ratio'] = visible_ratio
        
        # If less than 60% of face keypoints are visible, consider face as occluded
        if visible_ratio < 0.6:
            occlusion_features['face_occluded'] = True
            occlusion_features['occlusion_confidence'] = 1.0 - visible_ratio
    
    # Check hand proximity to face
    if NOSE < len(keypoints):
        nose_pos = keypoints[NOSE][:3]
        
        # Distance threshold (relative to keypoint scale)
        # We'll calculate reference distance based on head size
        reference_distance = 0.0
        reference_count = 0
        
        if NOSE < len(keypoints) and LEFT_EAR < len(keypoints):
            reference_distance += np.linalg.norm(keypoints[NOSE][:3] - keypoints[LEFT_EAR][:3])
            reference_count += 1
            
        if NOSE < len(keypoints) and RIGHT_EAR < len(keypoints):
            reference_distance += np.linalg.norm(keypoints[NOSE][:3] - keypoints[RIGHT_EAR][:3])
            reference_count += 1
            
        if reference_count > 0:
            reference_distance /= reference_count
            proximity_threshold = reference_distance * 1.2  # 1.2x head width
        else:
            # Fallback threshold if we can't calculate reference distance
            proximity_threshold = 0.3  # Arbitrary threshold
        
        for hand_idx in HAND_KEYPOINTS:
            if hand_idx < len(keypoints):
                hand_pos = keypoints[hand_idx][:3]
                hand_face_distance = np.linalg.norm(nose_pos - hand_pos)
                
                if hand_face_distance < proximity_threshold:
                    occlusion_features['hand_near_face'] = True
                    occlusion_features['face_occluded'] = True
                    # Calculate confidence based on proximity
                    proximity_ratio = 1.0 - (hand_face_distance / proximity_threshold)
                    occlusion_features['occlusion_confidence'] = max(
                        occlusion_features['occlusion_confidence'],
                        proximity_ratio
                    )
    
    return occlusion_features

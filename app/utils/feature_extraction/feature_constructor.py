"""Main module for constructing posture features from keypoints."""

import numpy as np
from typing import Dict, Any, List

from .bone_vectors import extract_bone_vectors, normalize_bone_vectors
from .angular_features import compute_angular_features
from .distance_features import compute_distance_features
from .face_occlusion import detect_face_occlusion
from .blanket_kick import detect_blanket_kick

class PostureFeatureConstructor:
    """Class for constructing posture features from MediaPipe keypoints."""
    
    def __init__(self):
        """Initialize the feature constructor."""
        pass
    
    def construct_features(self, keypoints: np.ndarray) -> Dict[str, Any]:
        """
        Construct comprehensive posture features from keypoints.
        
        Args:
            keypoints: Numpy array of shape (N, 3) or (N, 4) with keypoint coordinates [x, y, z, (visibility)]
            
        Returns:
            Dictionary containing all computed features
        """
        # Initialize features dictionary
        features = {
            'bone_vectors': {},
            'angular_features': {},
            'distance_features': {},
            'face_occlusion': {},
            'blanket_kick': {}
        }
        
        # 1. Extract bone vectors
        bone_vectors = extract_bone_vectors(keypoints)
        normalized_bone_vectors = normalize_bone_vectors(bone_vectors)
        features['bone_vectors'] = normalized_bone_vectors
        
        # 2. Compute angular features
        angular_features = compute_angular_features(keypoints, bone_vectors)
        features['angular_features'] = angular_features
        
        # 3. Compute distance features
        distance_features = compute_distance_features(keypoints, bone_vectors)
        features['distance_features'] = distance_features
        
        # 4. Detect face occlusion
        face_occlusion = detect_face_occlusion(keypoints)
        features['face_occlusion'] = face_occlusion
        
        # 5. Detect blanket kick
        blanket_kick = detect_blanket_kick(keypoints)
        features['blanket_kick'] = blanket_kick
        
        # 6. Create flattened feature vector for classification
        flat_features = self._flatten_features(features)
        features['feature_vector'] = flat_features
        
        return features
    
    def _flatten_features(self, feature_dict: Dict[str, Any]) -> np.ndarray:
        """
        Flatten the hierarchical feature dictionary into a 1D vector.
        
        Args:
            feature_dict: Dictionary containing all features
            
        Returns:
            1D numpy array of flattened features
        """
        flat_features = []
        
        # Add angular features
        for key in sorted(feature_dict['angular_features'].keys()):
            flat_features.append(feature_dict['angular_features'][key])
        
        # Add distance features
        for key in sorted(feature_dict['distance_features'].keys()):
            flat_features.append(feature_dict['distance_features'][key])
        
        # Add face occlusion features
        flat_features.append(float(feature_dict['face_occlusion']['face_occluded']))
        flat_features.append(feature_dict['face_occlusion']['occlusion_confidence'])
        flat_features.append(feature_dict['face_occlusion']['visible_face_keypoints_ratio'])
        flat_features.append(float(feature_dict['face_occlusion']['hand_near_face']))
        
        # Add blanket kick features
        flat_features.append(float(feature_dict['blanket_kick']['blanket_kicked']))
        flat_features.append(feature_dict['blanket_kick']['kick_confidence'])
        flat_features.append(float(feature_dict['blanket_kick']['feet_outside_blanket']))
        
        return np.array(flat_features)

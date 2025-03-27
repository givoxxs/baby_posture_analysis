"""Feature extraction module for baby posture analysis."""

from .feature_constructor import PostureFeatureConstructor
from .bone_vectors import extract_bone_vectors
from .angular_features import compute_angular_features
from .distance_features import compute_distance_features
from .face_occlusion import detect_face_occlusion
from .blanket_kick import detect_blanket_kick

__all__ = [
    'PostureFeatureConstructor',
    'extract_bone_vectors',
    'compute_angular_features',
    'compute_distance_features',
    'detect_face_occlusion',
    'detect_blanket_kick',
]

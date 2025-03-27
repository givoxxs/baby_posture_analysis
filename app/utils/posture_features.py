"""
Posture feature extraction utilities.

This module provides functions for extracting meaningful features from pose landmarks,
which are used for posture classification and risk analysis.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
import logging
from app.models.schemas import Point, PostureAnalysis
from app.utils.mediapipe_utils import PoseDetector

logger = logging.getLogger(__name__)

class PostureFeatureExtractor:
    """Extracts meaningful features from pose landmarks for posture analysis."""
    
    def __init__(self, pose_detector: PoseDetector):
        """
        Initialize the feature extractor.
        
        Args:
            pose_detector: PoseDetector instance for angle/vector calculations
        """
        self.pose_detector = pose_detector
    
    def extract_features(self, landmarks: Dict[str, Point]) -> Dict[str, Any]:
        """
        Extract all posture features from landmarks.
        
        Args:
            landmarks: Dictionary of landmarks from PoseDetector
            
        Returns:
            Dictionary of extracted features
        """
        if not landmarks:
            logger.warning("No landmarks provided to feature extractor")
            return {}
        
        features = {}
        
        # Extract bone vectors
        features.update(self.extract_bone_vectors(landmarks))
        
        # Extract angular features
        features.update(self.extract_angular_features(landmarks))
        
        # Extract distance features
        features.update(self.extract_distance_features(landmarks))
        
        # Extract face occlusion features
        features.update(self.detect_face_occlusion(landmarks))
        
        # Extract blanket kick features
        features.update(self.detect_blanket_kick(landmarks))
        
        return features
    
    def extract_bone_vectors(self, landmarks: Dict[str, Point]) -> Dict[str, Any]:
        """
        Extract and normalize bone vectors from landmarks.
        
        Args:
            landmarks: Dictionary of landmarks
            
        Returns:
            Dictionary of bone vectors
        """
        bone_pairs = [
            ("left_shoulder", "left_elbow", "left_upper_arm"),
            ("right_shoulder", "right_elbow", "right_upper_arm"),
            ("left_elbow", "left_wrist", "left_forearm"),
            ("right_elbow", "right_wrist", "right_forearm"),
            ("left_shoulder", "right_shoulder", "shoulders"),
            ("left_hip", "right_hip", "hips"),
            ("left_hip", "left_knee", "left_thigh"),
            ("right_hip", "right_knee", "right_thigh"),
            ("left_knee", "left_ankle", "left_shin"),
            ("right_knee", "right_ankle", "right_shin"),
            ("left_shoulder", "left_hip", "left_torso"),
            ("right_shoulder", "right_hip", "right_torso"),
            ("nose", "left_shoulder", "left_neck"),
            ("nose", "right_shoulder", "right_neck")
        ]
        
        vectors = {}
        missing_landmarks = set()
        
        for start, end, name in bone_pairs:
            if start in landmarks and end in landmarks:
                vector = self.pose_detector.calculate_vector(landmarks[start], landmarks[end])
                norm_vector = self.pose_detector.normalize_vector(vector)
                magnitude = np.linalg.norm(vector)
                
                vectors[f"{name}_vector"] = vector
                vectors[f"{name}_norm"] = norm_vector
                vectors[f"{name}_length"] = magnitude
            else:
                missing_landmarks.add(start if start not in landmarks else end)
        
        if missing_landmarks:
            logger.debug(f"Missing landmarks for bone vectors: {missing_landmarks}")
        
        return vectors
    
    def extract_angular_features(self, landmarks: Dict[str, Point]) -> Dict[str, float]:
        """
        Extract angular features from landmarks.
        
        Args:
            landmarks: Dictionary of landmarks
            
        Returns:
            Dictionary of angular features
        """
        angles = {}
        required_landmarks = {
            "head_body_angle": ["nose", "left_shoulder", "right_shoulder"],
            "left_arm_angle": ["left_shoulder", "left_elbow", "left_wrist"],
            "right_arm_angle": ["right_shoulder", "right_elbow", "right_wrist"],
            "left_leg_angle": ["left_hip", "left_knee", "left_ankle"],
            "right_leg_angle": ["right_hip", "right_knee", "right_ankle"],
            "body_tilt_angle": ["left_shoulder", "right_shoulder"]
        }
        
        # Head-body angle (angle between vertical axis and neck)
        if all(k in landmarks for k in ["nose", "left_shoulder", "right_shoulder"]):
            # Create a virtual mid-shoulder point
            mid_shoulder = Point(
                x=(landmarks["left_shoulder"].x + landmarks["right_shoulder"].x) / 2,
                y=(landmarks["left_shoulder"].y + landmarks["right_shoulder"].y) / 2,
                z=(landmarks["left_shoulder"].z + landmarks["right_shoulder"].z) / 2 
                if (landmarks["left_shoulder"].z is not None and landmarks["right_shoulder"].z is not None) 
                else None,
                visibility=1.0
            )
            
            # Create a virtual point directly above mid-shoulder (for vertical reference)
            vertical_reference = Point(
                x=mid_shoulder.x,
                y=mid_shoulder.y - 1.0,  # -1.0 because y increases downward in image
                z=mid_shoulder.z,
                visibility=1.0
            )
            
            head_body_angle = self.pose_detector.calculate_angle(
                vertical_reference, mid_shoulder, landmarks["nose"]
            )
            angles["head_body_angle"] = head_body_angle
        
        # Left arm angle
        if all(k in landmarks for k in ["left_shoulder", "left_elbow", "left_wrist"]):
            left_arm_angle = self.pose_detector.calculate_angle(
                landmarks["left_shoulder"], landmarks["left_elbow"], landmarks["left_wrist"]
            )
            angles["left_arm_angle"] = left_arm_angle
        
        # Right arm angle
        if all(k in landmarks for k in ["right_shoulder", "right_elbow", "right_wrist"]):
            right_arm_angle = self.pose_detector.calculate_angle(
                landmarks["right_shoulder"], landmarks["right_elbow"], landmarks["right_wrist"]
            )
            angles["right_arm_angle"] = right_arm_angle
        
        # Left leg angle
        if all(k in landmarks for k in ["left_hip", "left_knee", "left_ankle"]):
            left_leg_angle = self.pose_detector.calculate_angle(
                landmarks["left_hip"], landmarks["left_knee"], landmarks["left_ankle"]
            )
            angles["left_leg_angle"] = left_leg_angle
        
        # Right leg angle
        if all(k in landmarks for k in ["right_hip", "right_knee", "right_ankle"]):
            right_leg_angle = self.pose_detector.calculate_angle(
                landmarks["right_hip"], landmarks["right_knee"], landmarks["right_ankle"]
            )
            angles["right_leg_angle"] = right_leg_angle
        
        # Body tilt angle (angle between horizontal and shoulders)
        if all(k in landmarks for k in ["left_shoulder", "right_shoulder"]):
            # Create a virtual horizontal reference point
            horizontal_reference = Point(
                x=landmarks["left_shoulder"].x + 1.0,
                y=landmarks["left_shoulder"].y,
                z=landmarks["left_shoulder"].z,
                visibility=1.0
            )
            
            body_tilt_angle = self.pose_detector.calculate_angle(
                horizontal_reference, landmarks["left_shoulder"], landmarks["right_shoulder"]
            )
            angles["body_tilt_angle"] = abs(90 - body_tilt_angle)  # Deviation from vertical
        
        return angles
    
    def extract_distance_features(self, landmarks: Dict[str, Point]) -> Dict[str, float]:
        """
        Extract distance-based features from landmarks.
        
        Args:
            landmarks: Dictionary of landmarks
            
        Returns:
            Dictionary of distance features
        """
        distances = {}
        
        # Distance from nose to ground plane
        if "nose" in landmarks:
            ground_plane = self.pose_detector.estimate_ground_plane(landmarks)
            nose_point = np.array([
                landmarks["nose"].x,
                landmarks["nose"].y,
                landmarks["nose"].z if landmarks["nose"].z is not None else 0
            ])
            
            # Project nose onto ground plane
            origin = np.array([0, 0, 0])
            nose_to_ground = np.abs(np.dot(nose_point - origin, ground_plane))
            distances["nose_to_ground"] = nose_to_ground
        
        # Distance between shoulders (for side lying detection)
        if "left_shoulder" in landmarks and "right_shoulder" in landmarks:
            shoulder_distance = self.pose_detector.calculate_distance(
                landmarks["left_shoulder"], landmarks["right_shoulder"]
            )
            distances["shoulder_distance"] = shoulder_distance
        
        # Distance from hands to face (for face occlusion detection)
        if "nose" in landmarks:
            for hand in ["left_wrist", "right_wrist"]:
                if hand in landmarks:
                    hand_to_face = self.pose_detector.calculate_distance(
                        landmarks["nose"], landmarks[hand]
                    )
                    distances[f"{hand}_to_face"] = hand_to_face
        
        # Calculate relative depth of landmarks (z-coordinate differences)
        if all(k in landmarks for k in ["nose", "left_shoulder", "right_shoulder"]):
            if all(landmarks[k].z is not None for k in ["nose", "left_shoulder", "right_shoulder"]):
                # Average shoulder z position
                avg_shoulder_z = (landmarks["left_shoulder"].z + landmarks["right_shoulder"].z) / 2
                # Difference in depth between nose and shoulders
                distances["nose_depth_difference"] = landmarks["nose"].z - avg_shoulder_z
        
        return distances
    
    def detect_face_occlusion(self, landmarks: Dict[str, Point]) -> Dict[str, Any]:
        """
        Detect face occlusion based on visibility of face landmarks and hand proximity.
        
        Args:
            landmarks: Dictionary of landmarks
            
        Returns:
            Dictionary of face occlusion features
        """
        face_occlusion = {
            "is_face_occluded": False,
            "occlusion_confidence": 0.0,
            "occlusion_reason": "none"
        }
        
        # Check visibility of face landmarks
        face_landmarks = ["nose", "left_eye", "right_eye", "mouth_left", "mouth_right"]
        visible_face_landmarks = [
            lm for lm in face_landmarks 
            if lm in landmarks and landmarks[lm].visibility > 0.5
        ]
        
        face_visibility_ratio = len(visible_face_landmarks) / len(face_landmarks)
        
        # Check hand proximity to face
        hand_near_face = False
        hand_distance_threshold = 0.15  # Normalized distance threshold
        
        for hand in ["left_wrist", "right_wrist"]:
            if hand in landmarks and "nose" in landmarks:
                distance = self.pose_detector.calculate_distance(landmarks[hand], landmarks["nose"])
                if distance < hand_distance_threshold:
                    hand_near_face = True
                    face_occlusion["occlusion_reason"] = f"{hand.split('_')[0]}_hand_near_face"
        
        # Detect face down position based on z-coordinates
        face_down = False
        if "nose" in landmarks and all(k in landmarks for k in ["left_shoulder", "right_shoulder"]):
            if (landmarks["nose"].z is not None and 
                landmarks["left_shoulder"].z is not None and 
                landmarks["right_shoulder"].z is not None):
                
                avg_shoulder_z = (landmarks["left_shoulder"].z + landmarks["right_shoulder"].z) / 2
                if landmarks["nose"].z > avg_shoulder_z + 0.05:  # Nose is deeper than shoulders
                    face_down = True
                    face_occlusion["occlusion_reason"] = "face_down"
        
        # Determine occlusion status
        if face_visibility_ratio < 0.6 or hand_near_face or face_down:
            face_occlusion["is_face_occluded"] = True
            face_occlusion["occlusion_confidence"] = max(
                1.0 - face_visibility_ratio,  # Lower visibility = higher occlusion confidence
                0.7 if hand_near_face else 0.0,
                0.9 if face_down else 0.0
            )
        
        return face_occlusion
    
    def detect_blanket_kick(self, landmarks: Dict[str, Point]) -> Dict[str, Any]:
        """
        Detect if the baby is kicking off blankets based on foot positions.
        
        Args:
            landmarks: Dictionary of landmarks
            
        Returns:
            Dictionary of blanket kick features
        """
        blanket_kick = {
            "is_kicking_blanket": False,
            "kick_confidence": 0.0
        }
        
        # Estimate blanket region (assuming blanket covers up to hips/knees)
        if all(k in landmarks for k in ["left_hip", "right_hip"]):
            # Get average y position of hips as blanket boundary
            avg_hip_y = (landmarks["left_hip"].y + landmarks["right_hip"].y) / 2
            
            # Check if feet are above the hip level
            feet_landmarks = ["left_ankle", "right_ankle", "left_foot_index", "right_foot_index"]
            feet_above_hips = []
            
            for foot in feet_landmarks:
                if foot in landmarks:
                    # In image coordinates, smaller y is higher in the image (above)
                    if landmarks[foot].y < avg_hip_y:
                        feet_above_hips.append(foot)
            
            # If any feet are above hips, baby might be kicking blanket
            if feet_above_hips:
                blanket_kick["is_kicking_blanket"] = True
                blanket_kick["kick_confidence"] = min(1.0, len(feet_above_hips) / len(feet_landmarks))
            
        return blanket_kick

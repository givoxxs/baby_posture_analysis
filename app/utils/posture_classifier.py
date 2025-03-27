"""
Posture classification utilities.

This module provides functions for classifying baby postures based on extracted features.
It uses rule-based classification to determine the posture type and risk level.
"""

from typing import Dict, Any, Tuple, List, Optional
import logging
import numpy as np
from app.models.schemas import RiskLevel, PostureAnalysis

logger = logging.getLogger(__name__)

class PostureClassifier:
    """Classifies baby postures based on extracted features."""
    
    # Define posture types
    POSTURE_TYPES = {
        "lying_on_back": "Baby is lying on back (supine position)",
        "lying_on_stomach": "Baby is lying on stomach (prone position)",
        "lying_on_side": "Baby is lying on side (lateral position)",
        "face_down": "Baby's face is downward/pressed against the surface",
        "limbs_folded": "Baby's limbs are folded against body"
    }
    
    def __init__(self):
        """Initialize the posture classifier."""
        pass
    
    def classify(self, features: Dict[str, Any]) -> Tuple[str, float, Dict[str, Any]]:
        """
        Classify the posture based on extracted features.
        
        Args:
            features: Dictionary of extracted features from PostureFeatureExtractor
            
        Returns:
            Tuple containing:
                - Posture type string
                - Confidence score (0.0 to 1.0)
                - Additional classification details
        """
        if not features:
            logger.warning("No features provided for classification")
            return "unknown", 0.0, {}
        
        # Apply rule-based classification
        posture_scores = self._apply_rules(features)
        
        # Get the posture with the highest score
        if posture_scores:
            posture_type = max(posture_scores.items(), key=lambda x: x[1][0])
            return posture_type[0], posture_type[1][0], posture_type[1][1]
        else:
            return "unknown", 0.0, {}
    
    def _apply_rules(self, features: Dict[str, Any]) -> Dict[str, Tuple[float, Dict[str, Any]]]:
        """
        Apply rule-based classification to determine posture types.
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            Dictionary mapping posture types to (confidence, details) tuples
        """
        posture_scores = {}
        details = {}
        
        # Check for face down posture (highest priority)
        if self._is_face_down(features):
            confidence = min(features.get("face_occlusion", {}).get("occlusion_confidence", 0.0) * 1.2, 1.0)
            details = {
                "reason": "Face is occluded or pressed against surface",
                "occlusion_details": features.get("face_occlusion", {})
            }
            posture_scores["face_down"] = (confidence, details)
        
        # Check for lying on stomach
        if self._is_lying_on_stomach(features):
            confidence = self._get_stomach_lying_confidence(features)
            details = {
                "reason": "Body orientation suggests prone position",
                "angular_details": {k: v for k, v in features.items() if "angle" in k}
            }
            posture_scores["lying_on_stomach"] = (confidence, details)
        
        # Check for lying on side
        if self._is_lying_on_side(features):
            confidence = self._get_side_lying_confidence(features)
            details = {
                "reason": "Body orientation suggests lateral position",
                "shoulder_distance": features.get("shoulder_distance", 0),
                "tilt_angle": features.get("body_tilt_angle", 0)
            }
            posture_scores["lying_on_side"] = (confidence, details)
        
        # Check for limb folding
        if self._has_folded_limbs(features):
            confidence = self._get_limb_folding_confidence(features)
            details = {
                "reason": "One or more limbs are folded",
                "arm_angles": {
                    "left": features.get("left_arm_angle", 0),
                    "right": features.get("right_arm_angle", 0)
                },
                "leg_angles": {
                    "left": features.get("left_leg_angle", 0),
                    "right": features.get("right_leg_angle", 0)
                }
            }
            posture_scores["limbs_folded"] = (confidence, details)
        
        # Default to lying on back if no other posture is detected with sufficient confidence
        if not any(score > 0.5 for score, _ in posture_scores.values()):
            details = {
                "reason": "Default classification as no other posture detected with confidence"
            }
            posture_scores["lying_on_back"] = (0.6, details)
        
        return posture_scores
    
    def _is_face_down(self, features: Dict[str, Any]) -> bool:
        """
        Determine if baby's face is pressed down against the surface.
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            True if face is likely pressed against surface, False otherwise
        """
        # Check if face occlusion is detected
        face_occlusion = features.get("face_occlusion", {})
        if face_occlusion.get("is_face_occluded", False):
            if face_occlusion.get("occlusion_reason") == "face_down":
                return True
            elif face_occlusion.get("occlusion_confidence", 0) > 0.7:
                return True
        
        # Check nose depth relative to shoulders
        if "nose_depth_difference" in features and features["nose_depth_difference"] > 0.05:
            return True
        
        return False
    
    def _is_lying_on_stomach(self, features: Dict[str, Any]) -> bool:
        """
        Determine if baby is lying on stomach (prone position).
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            True if lying on stomach, False otherwise
        """
        # Check head body angle
        head_body_angle = features.get("head_body_angle", 90)
        
        # In prone position, head is typically at an angle relative to vertical axis
        if head_body_angle < 30 or head_body_angle > 150:
            return True
        
        # Check if body is relatively flat (small tilt angle)
        body_tilt = features.get("body_tilt_angle", 90)
        if body_tilt < 20:
            return True
        
        return False
    
    def _is_lying_on_side(self, features: Dict[str, Any]) -> bool:
        """
        Determine if baby is lying on side (lateral position).
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            True if lying on side, False otherwise
        """
        # Check body tilt angle
        body_tilt = features.get("body_tilt_angle", 0)
        if body_tilt > 45:  # Significant deviation from vertical
            return True
        
        # Check shoulder distance (appears shorter when viewed from side)
        # Assuming normal shoulder distance is around 0.2 in normalized coordinates
        if "shoulder_distance" in features:
            if features["shoulder_distance"] < 0.1:  # Significantly foreshortened
                return True
        
        return False
    
    def _has_folded_limbs(self, features: Dict[str, Any]) -> bool:
        """
        Determine if baby has folded limbs.
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            True if limbs are folded, False otherwise
        """
        # Check arm angles
        left_arm_angle = features.get("left_arm_angle", 180)
        right_arm_angle = features.get("right_arm_angle", 180)
        
        # Check leg angles
        left_leg_angle = features.get("left_leg_angle", 180)
        right_leg_angle = features.get("right_leg_angle", 180)
        
        # Folded limbs have acute angles at joints
        arms_folded = (left_arm_angle < 90 or right_arm_angle < 90)
        legs_folded = (left_leg_angle < 90 or right_leg_angle < 90)
        
        return arms_folded or legs_folded
    
    def _get_stomach_lying_confidence(self, features: Dict[str, Any]) -> float:
        """Calculate confidence for lying on stomach classification."""
        head_body_angle = features.get("head_body_angle", 90)
        body_tilt = features.get("body_tilt_angle", 90)
        
        # Convert angles to confidence scores
        head_confidence = max(0, 1 - abs(head_body_angle - 0) / 30)
        tilt_confidence = max(0, 1 - body_tilt / 20)
        
        # Combine confidence scores
        confidence = max(head_confidence, tilt_confidence)
        
        return min(1.0, confidence)
    
    def _get_side_lying_confidence(self, features: Dict[str, Any]) -> float:
        """Calculate confidence for lying on side classification."""
        body_tilt = features.get("body_tilt_angle", 0)
        shoulder_distance = features.get("shoulder_distance", 0.2)
        
        # Convert measurements to confidence scores
        tilt_confidence = min(1.0, body_tilt / 90)
        shoulder_confidence = max(0, 1 - (shoulder_distance - 0.05) / 0.15)
        
        # Combine confidence scores
        confidence = max(tilt_confidence, shoulder_confidence)
        
        return min(1.0, confidence)
    
    def _get_limb_folding_confidence(self, features: Dict[str, Any]) -> float:
        """Calculate confidence for limb folding classification."""
        left_arm_angle = features.get("left_arm_angle", 180)
        right_arm_angle = features.get("right_arm_angle", 180)
        left_leg_angle = features.get("left_leg_angle", 180)
        right_leg_angle = features.get("right_leg_angle", 180)
        
        # Convert angles to confidence scores
        left_arm_conf = max(0, 1 - left_arm_angle / 90)
        right_arm_conf = max(0, 1 - right_arm_angle / 90)
        left_leg_conf = max(0, 1 - left_leg_angle / 90)
        right_leg_conf = max(0, 1 - right_leg_angle / 90)
        
        # Use the maximum confidence from any limb
        confidence = max(left_arm_conf, right_arm_conf, left_leg_conf, right_leg_conf)
        
        return min(1.0, confidence)

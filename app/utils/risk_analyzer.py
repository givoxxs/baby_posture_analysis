"""
Risk analysis for baby postures.

This module provides functions for analyzing the risk level of detected postures.
"""

from typing import Dict, Any, Tuple, List, Optional
import logging
from app.models.schemas import RiskLevel, PostureAnalysis

logger = logging.getLogger(__name__)

class RiskAnalyzer:
    """Analyzes risk levels of baby postures."""
    
    # Risk score thresholds
    RISK_THRESHOLDS = {
        RiskLevel.LOW: 3.0,
        RiskLevel.MEDIUM: 5.0,
        RiskLevel.HIGH: 7.0,
        RiskLevel.CRITICAL: 9.0
    }
    
    # Base risk scores for different posture types
    BASE_RISK_SCORES = {
        "face_down": 9.0,
        "lying_on_stomach": 7.0,
        "lying_on_side": 4.0,
        "limbs_folded": 2.0,
        "lying_on_back": 1.0,
        "unknown": 5.0
    }
    
    def __init__(self):
        """Initialize risk analyzer."""
        pass
    
    def analyze_risk(
        self, 
        posture_type: str, 
        confidence: float, 
        features: Dict[str, Any]
    ) -> Tuple[RiskLevel, float, PostureAnalysis]:
        """
        Analyze the risk level of a detected posture.
        
        Args:
            posture_type: Detected posture type
            confidence: Detection confidence
            features: Extracted posture features
            
        Returns:
            Tuple containing:
                - Risk level
                - Risk score (0-10)
                - Detailed posture analysis
        """
        # Get base risk score for detected posture
        risk_score = self.BASE_RISK_SCORES.get(posture_type, 5.0)
        
        # Adjust risk based on specific features
        risk_adjustments = self._calculate_risk_adjustments(posture_type, features)
        
        # Apply adjustments to risk score
        for adjustment, value in risk_adjustments.items():
            risk_score += value
        
        # Scale by confidence (low confidence should reduce extreme risk scores)
        confidence_factor = 0.5 + (0.5 * confidence)  # Range from 0.5 to 1.0
        risk_score = ((risk_score - 5.0) * confidence_factor) + 5.0
        
        # Ensure score is within bounds
        risk_score = max(0.0, min(10.0, risk_score))
        
        # Determine risk level
        risk_level = self._get_risk_level(risk_score)
        
        # Generate detailed analysis
        analysis = self._generate_analysis(posture_type, risk_level, features, risk_adjustments)
        
        return risk_level, risk_score, analysis
    
    def _calculate_risk_adjustments(
        self, 
        posture_type: str, 
        features: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate risk adjustments based on specific features.
        
        Args:
            posture_type: Detected posture type
            features: Extracted posture features
            
        Returns:
            Dictionary of risk adjustments with explanations
        """
        adjustments = {}
        
        # Check for face occlusion (major risk factor)
        face_occlusion = features.get("face_occlusion", {})
        if face_occlusion.get("is_face_occluded", False):
            occlusion_conf = face_occlusion.get("occlusion_confidence", 0.5)
            adjustments["face_occlusion"] = 3.0 * occlusion_conf
        
        # Check for folded limbs which might restrict movement
        if "left_arm_angle" in features and features["left_arm_angle"] < 45:
            adjustments["left_arm_folded"] = 0.5
        
        if "right_arm_angle" in features and features["right_arm_angle"] < 45:
            adjustments["right_arm_folded"] = 0.5
        
        if "left_leg_angle" in features and features["left_leg_angle"] < 45:
            adjustments["left_leg_folded"] = 0.5
        
        if "right_leg_angle" in features and features["right_leg_angle"] < 45:
            adjustments["right_leg_folded"] = 0.5
        
        # Check for blanket kicking (comfort/temperature risk)
        if features.get("blanket_kick", {}).get("is_kicking_blanket", False):
            kick_conf = features.get("blanket_kick", {}).get("kick_confidence", 0.5)
            adjustments["blanket_kicked_off"] = 1.0 * kick_conf
        
        # For prone positions, check if face is to the side (safer) vs. down (riskier)
        if posture_type == "lying_on_stomach" and not face_occlusion.get("is_face_occluded", False):
            # Face not occluded in prone position is better than occluded
            adjustments["face_clear_while_prone"] = -2.0
        
        return adjustments
    
    def _get_risk_level(self, risk_score: float) -> RiskLevel:
        """
        Convert risk score to risk level.
        
        Args:
            risk_score: Numerical risk score (0-10)
            
        Returns:
            Risk level enum value
        """
        if risk_score >= self.RISK_THRESHOLDS[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif risk_score >= self.RISK_THRESHOLDS[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif risk_score >= self.RISK_THRESHOLDS[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_analysis(
        self, 
        posture_type: str, 
        risk_level: RiskLevel, 
        features: Dict[str, Any],
        adjustments: Dict[str, float]
    ) -> PostureAnalysis:
        """
        Generate detailed posture analysis.
        
        Args:
            posture_type: Detected posture type
            risk_level: Determined risk level
            features: Extracted posture features
            adjustments: Risk adjustments that were applied
            
        Returns:
            Detailed posture analysis
        """
        # Determine face position
        face_position = self._determine_face_position(posture_type, features)
        
        # Determine limb positions
        limb_positions = self._determine_limb_positions(features)
        
        # Determine body orientation
        body_orientation = self._determine_body_orientation(posture_type, features)
        
        # Identify safety concerns
        safety_concerns = self._identify_safety_concerns(posture_type, risk_level, features, adjustments)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(posture_type, risk_level, safety_concerns)
        
        return PostureAnalysis(
            face_position=face_position,
            limb_positions=limb_positions,
            body_orientation=body_orientation,
            safety_concerns=safety_concerns,
            recommendations=recommendations
        )
    
    def _determine_face_position(self, posture_type: str, features: Dict[str, Any]) -> str:
        """Determine the position of the baby's face."""
        face_occlusion = features.get("face_occlusion", {})
        
        if face_occlusion.get("is_face_occluded", False):
            if face_occlusion.get("occlusion_reason", "") == "face_down":
                return "face_down"
            elif "hand" in face_occlusion.get("occlusion_reason", ""):
                return "covered_by_hand"
            else:
                return "occluded"
                
        if posture_type == "lying_on_side":
            return "turned_to_side"
        elif posture_type == "lying_on_stomach":
            return "turned_to_side"
        elif posture_type == "lying_on_back":
            return "facing_up"
        
        return "unknown"
    
    def _determine_limb_positions(self, features: Dict[str, Any]) -> List[str]:
        """Determine positions of baby's limbs."""
        positions = []
        
        # Check arm positions
        left_arm_angle = features.get("left_arm_angle", 180)
        right_arm_angle = features.get("right_arm_angle", 180)
        
        if left_arm_angle < 45 and right_arm_angle < 45:
            positions.append("both_arms_folded")
        elif left_arm_angle < 45:
            positions.append("left_arm_folded")
        elif right_arm_angle < 45:
            positions.append("right_arm_folded")
        
        if left_arm_angle > 160 and right_arm_angle > 160:
            positions.append("arms_extended")
            
        # Check leg positions
        left_leg_angle = features.get("left_leg_angle", 180)
        right_leg_angle = features.get("right_leg_angle", 180)
        
        if left_leg_angle < 45 and right_leg_angle < 45:
            positions.append("both_legs_folded")
        elif left_leg_angle < 45:
            positions.append("left_leg_folded")
        elif right_leg_angle < 45:
            positions.append("right_leg_folded")
        
        if left_leg_angle > 160 and right_leg_angle > 160:
            positions.append("legs_extended")
            
        # Check for blanket kicking
        if features.get("blanket_kick", {}).get("is_kicking_blanket", False):
            positions.append("kicking_blanket")
            
        return positions
    
    def _determine_body_orientation(self, posture_type: str, features: Dict[str, Any]) -> str:
        """Determine overall body orientation."""
        if posture_type == "lying_on_back":
            return "supine"
        elif posture_type == "lying_on_stomach":
            return "prone"
        elif posture_type == "lying_on_side":
            # Determine which side based on shoulder coordinates
            if "left_shoulder" in features and "right_shoulder" in features:
                if features.get("left_shoulder", {}).get("y", 0) < features.get("right_shoulder", {}).get("y", 0):
                    return "left_side"
                else:
                    return "right_side"
            return "lateral"
        
        return "unknown"
    
    def _identify_safety_concerns(
        self,
        posture_type: str,
        risk_level: RiskLevel,
        features: Dict[str, Any],
        adjustments: Dict[str, float]
    ) -> List[str]:
        """Identify safety concerns based on posture and risk level."""
        concerns = []
        
        # Face occlusion is a major concern
        if features.get("face_occlusion", {}).get("is_face_occluded", False):
            if features.get("face_occlusion", {}).get("occlusion_reason") == "face_down":
                concerns.append("face_pressed_against_surface")
            else:
                concerns.append("face_partially_obstructed")
        
        # Prone position concerns
        if posture_type == "lying_on_stomach":
            concerns.append("prone_position_breathing_risk")
        
        # Folded limbs concerns
        if "left_arm_folded" in adjustments or "right_arm_folded" in adjustments:
            concerns.append("restricted_arm_movement")
            
        if "left_leg_folded" in adjustments or "right_leg_folded" in adjustments:
            concerns.append("restricted_leg_movement")
        
        # Blanket concerns
        if "blanket_kicked_off" in adjustments:
            concerns.append("temperature_regulation")
            
        return concerns
    
    def _generate_recommendations(
        self,
        posture_type: str,
        risk_level: RiskLevel,
        safety_concerns: List[str]
    ) -> List[str]:
        """Generate safety recommendations based on identified concerns."""
        recommendations = []
        
        if "face_pressed_against_surface" in safety_concerns:
            recommendations.append("reposition_immediately")
            recommendations.append("ensure_clear_airway")
            
        if "prone_position_breathing_risk" in safety_concerns:
            if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                recommendations.append("turn_to_back_or_side")
            else:
                recommendations.append("monitor_breathing_closely")
                
        if "restricted_arm_movement" in safety_concerns or "restricted_leg_movement" in safety_concerns:
            recommendations.append("check_for_discomfort")
            recommendations.append("ensure_limbs_not_trapped")
            
        if "temperature_regulation" in safety_concerns:
            recommendations.append("check_room_temperature")
            recommendations.append("adjust_blanket_coverage")
        
        # General recommendations based on risk level
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("immediate_attention_required")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("frequent_monitoring_needed")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("regular_checks_advised")
            
        return recommendations

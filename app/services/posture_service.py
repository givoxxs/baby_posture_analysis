"""
Service for posture analysis operations.
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from app.utils.posture_utils import (
    detect_face_down,
    detect_blanket_kicked,
    compute_angles,
    analyze_risk
)


class PostureService:
    """Service for posture analysis."""
    
    def analyze_from_keypoints(self, keypoints_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze posture from keypoints data."""
        # Extract features from keypoints
        keypoints = keypoints_data.get("keypoints", [])
        joint_angles = keypoints_data.get("joint_angles", {})
        
        if not keypoints:
            return {
                "posture_type": "Unknown",
                "risk_score": 0,
                "confidence": 0,
                "details": {},
                "reasons": ["No keypoints detected"]
            }
        
        # Extract posture features
        features = self._extract_features(keypoints, joint_angles)
        
        # Analyze posture
        posture_type, risk_score, confidence, details, reasons = self._classify_posture(features)
        
        # Prepare body alignment data
        body_alignment = self._get_body_alignment(features)
        
        # Identify issues and recommendations
        issues, recommendations = self._get_issues_and_recommendations(features, posture_type, risk_score)
        
        return {
            "posture_type": posture_type,
            "risk_score": risk_score,
            "confidence": confidence * 100,  # Convert to percentage
            "details": details,
            "reasons": reasons,
            "body_alignment": body_alignment,
            "issues": issues,
            "recommendations": recommendations
        }
        
    def _extract_features(self, keypoints: List[Dict], joint_angles: Dict[str, float]) -> Dict[str, Any]:
        """Extract features from keypoints and angles."""
        # Convert keypoints to numpy array for easier processing
        keypoints_array = {kp["id"]: (kp["x"], kp["y"], kp["z"], kp["visibility"]) for kp in keypoints}
        
        # Detect face down
        face_down = detect_face_down(keypoints_array)
        
        # Detect blanket kicked
        blanket_kicked = detect_blanket_kicked(keypoints_array)
        
        # Compute angles (using simplified approach based on the documentation provided)
        head_angle, arm_angles, leg_angles, torso_angle = compute_angles(keypoints_array)
        
        return {
            "head_angle": head_angle,
            "arm_angles": arm_angles,
            "leg_angles": leg_angles,
            "torso_angle": torso_angle,
            "face_down": face_down,
            "blanket_kicked": blanket_kicked
        }
        
    def _classify_posture(self, features: Dict[str, Any]) -> Tuple[str, float, float, Dict[str, bool], List[str]]:
        """Classify posture based on extracted features."""
        # Simple rule-based classification
        reasons = []
        details = {
            "face_down": features["face_down"],
            "prone": features["head_angle"] < 30,
            "side_lying": features["torso_angle"] > 45,
            "limbs_bent": any(angle < 45 for angle in features["arm_angles"].values()) or 
                          any(angle < 45 for angle in features["leg_angles"].values()),
            "blanket_kicked": features["blanket_kicked"]
        }
        
        # Determine posture type and risk
        if details["face_down"]:
            posture_type = "Nguy hiểm"
            risk_score = 9.5
            confidence = 0.9
            reasons.append("Trẻ đang úp mặt, có nguy cơ nghẹt thở")
        elif details["prone"]:
            posture_type = "Có nguy cơ"
            risk_score = 7.5
            confidence = 0.8
            reasons.append("Trẻ đang nằm sấp, có thể xoay và úp mặt")
        elif details["side_lying"]:
            posture_type = "Có nguy cơ"
            risk_score = 4.0
            confidence = 0.7
            reasons.append("Trẻ đang nằm nghiêng, có thể lật úp")
        else:
            posture_type = "An toàn"
            risk_score = 2.0
            confidence = 0.75
            reasons.append("Tư thế nằm an toàn")
            
        # Add additional reasons
        if details["limbs_bent"]:
            reasons.append("Tay hoặc chân gấp lại")
            risk_score += 0.5
            
        if details["blanket_kicked"]:
            reasons.append("Đạp chăn, có thể bị lạnh")
            risk_score += 0.5
            
        # Ensure risk score is within bounds
        risk_score = min(max(risk_score, 1.0), 10.0)
        
        return posture_type, risk_score, confidence, details, reasons
    
    def _get_body_alignment(self, features: Dict[str, Any]) -> Dict[str, str]:
        """Evaluate body alignment based on features."""
        alignment = {}
        
        # Head alignment
        head_angle = features["head_angle"]
        if head_angle < 15:
            alignment["head_position"] = "poor"
        elif head_angle < 30:
            alignment["head_position"] = "fair"
        else:
            alignment["head_position"] = "good"
        
        # Spine alignment
        torso_angle = features["torso_angle"]
        if torso_angle > 60:
            alignment["spine_alignment"] = "poor"
        elif torso_angle > 30:
            alignment["spine_alignment"] = "fair"
        else:
            alignment["spine_alignment"] = "good"
        
        # Arms alignment
        arm_angles = features["arm_angles"]
        avg_arm_angle = sum(arm_angles.values()) / len(arm_angles) if arm_angles else 0
        if avg_arm_angle < 30:
            alignment["arms_position"] = "poor"
        elif avg_arm_angle < 60:
            alignment["arms_position"] = "fair"
        else:
            alignment["arms_position"] = "good"
            
        # Legs alignment
        leg_angles = features["leg_angles"]
        avg_leg_angle = sum(leg_angles.values()) / len(leg_angles) if leg_angles else 0
        if avg_leg_angle < 30:
            alignment["legs_position"] = "poor"
        elif avg_leg_angle < 60:
            alignment["legs_position"] = "fair"
        else:
            alignment["legs_position"] = "good"
        
        return alignment
    
    def _get_issues_and_recommendations(self, features: Dict[str, Any], posture_type: str, risk_score: float) -> Tuple[List[str], List[str]]:
        """Generate issues and recommendations based on posture analysis."""
        issues = []
        recommendations = []
        
        # Issues based on posture type
        if posture_type == "Nguy hiểm":
            issues.append("Tư thế nằm nguy hiểm, có nguy cơ cao gây nghẹt thở")
            recommendations.append("Lật trẻ lại ngay lập tức vào tư thế nằm ngửa")
            recommendations.append("Theo dõi trẻ thường xuyên")
            
        elif posture_type == "Có nguy cơ":
            issues.append("Tư thế nằm có nguy cơ, cần theo dõi")
            recommendations.append("Điều chỉnh tư thế của trẻ về tư thế an toàn hơn")
            recommendations.append("Kiểm tra trẻ thường xuyên")
            
        # Issues based on specific features
        if features["face_down"]:
            issues.append("Trẻ đang úp mặt xuống")
            recommendations.append("Lật trẻ lại ngay hoặc xoay đầu trẻ sang một bên")
            
        if features["blanket_kicked"]:
            issues.append("Trẻ đã đạp chăn, có thể bị lạnh")
            recommendations.append("Đắp lại chăn cho trẻ và sử dụng chăn chần")
            
        if any(angle < 45 for angle in features["arm_angles"].values()) or any(angle < 45 for angle in features["leg_angles"].values()):
            issues.append("Tay hoặc chân gấp ở tư thế không tự nhiên")
            recommendations.append("Nhẹ nhàng điều chỉnh tay/chân về tư thế tự nhiên hơn")
        
        return issues, recommendations

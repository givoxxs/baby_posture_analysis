"""
Utility functions for posture analysis.
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Optional, Any


def detect_face_down(keypoints: Dict[int, Tuple]) -> bool:
    """
    Detect if the baby is face down.
    
    Args:
        keypoints: Dictionary of keypoints with their coordinates and visibility

    Returns:
        True if face down, False otherwise
    """
    # Check if nose is visible
    nose_visible = False
    if 0 in keypoints:  # 0 is the nose keypoint ID
        _, _, _, visibility = keypoints[0]
        nose_visible = visibility > 0.5
    
    # If nose is not visible, check head orientation
    if not nose_visible:
        # Check for head-torso angle indicating face down position
        if all(k in keypoints for k in [0, 11, 12]):  # nose, left_shoulder, right_shoulder
            nose = keypoints[0]
            left_shoulder = keypoints[11]
            right_shoulder = keypoints[12]
            
            # Calculate midpoint of shoulders
            shoulder_mid_x = (left_shoulder[0] + right_shoulder[0]) / 2
            shoulder_mid_y = (left_shoulder[1] + right_shoulder[1]) / 2
            
            # Vector from shoulder midpoint to nose
            v_shoulder_nose = [nose[0] - shoulder_mid_x, nose[1] - shoulder_mid_y]
            
            # Vector pointing upward
            v_vertical = [0, -1]
            
            # Calculate the angle between these vectors
            dot_product = v_shoulder_nose[0] * v_vertical[0] + v_shoulder_nose[1] * v_vertical[1]
            mag_shoulder_nose = math.sqrt(v_shoulder_nose[0]**2 + v_shoulder_nose[1]**2)
            mag_vertical = 1  # Unit vector
            
            cos_angle = dot_product / (mag_shoulder_nose * mag_vertical)
            angle_radians = math.acos(max(-1, min(1, cos_angle)))
            angle_degrees = math.degrees(angle_radians)
            
            # If the angle is less than 15 degrees, consider it face down
            if angle_degrees < 15:
                return True
    
    return False


def detect_blanket_kicked(keypoints: Dict[int, Tuple]) -> bool:
    """
    Detect if the baby has kicked off the blanket.
    
    Simple approach: If lower body parts (hips, knees, ankles) are visible, 
    consider the blanket kicked off.
    
    Args:
        keypoints: Dictionary of keypoints with their coordinates and visibility

    Returns:
        True if blanket kicked, False otherwise
    """
    # Check if lower body parts are visible
    lower_body_parts = [23, 24, 25, 26, 27, 28]  # hips, knees, ankles
    visible_parts = 0
    
    for part_id in lower_body_parts:
        if part_id in keypoints:
            _, _, _, visibility = keypoints[part_id]
            if visibility > 0.5:
                visible_parts += 1
    
    # If more than half of lower body parts are visible, consider blanket kicked
    return visible_parts >= 3


def compute_angles(keypoints: Dict[int, Tuple]) -> Tuple[float, Dict[str, float], Dict[str, float], float]:
    """
    Compute key angles for posture analysis.
    
    Args:
        keypoints: Dictionary of keypoints with their coordinates and visibility

    Returns:
        Tuple containing:
        - head_angle: angle between head and vertical axis
        - arm_angles: dictionary of arm joint angles
        - leg_angles: dictionary of leg joint angles
        - torso_angle: angle between torso and horizontal axis
    """
    # Initialize return values
    head_angle = 90.0  # Default to 90 degrees (neutral position)
    arm_angles = {}
    leg_angles = {}
    torso_angle = 0.0  # Default to 0 degrees (horizontal)
    
    # Calculate head angle
    if all(k in keypoints for k in [0, 11, 12]):  # nose, left_shoulder, right_shoulder
        nose = keypoints[0][:2]  # x, y coordinates
        left_shoulder = keypoints[11][:2]
        right_shoulder = keypoints[12][:2]
        
        # Shoulder midpoint
        shoulder_mid = [(left_shoulder[0] + right_shoulder[0]) / 2, 
                        (left_shoulder[1] + right_shoulder[1]) / 2]
        
        # Vector from shoulder midpoint to nose
        v_shoulder_nose = [nose[0] - shoulder_mid[0], nose[1] - shoulder_mid[1]]
        
        # Vector pointing upward
        v_vertical = [0, -1]
        
        # Calculate angle
        dot_product = v_shoulder_nose[0] * v_vertical[0] + v_shoulder_nose[1] * v_vertical[1]
        mag_shoulder_nose = math.sqrt(v_shoulder_nose[0]**2 + v_shoulder_nose[1]**2)
        mag_vertical = 1  # Unit vector
        
        cos_angle = dot_product / (mag_shoulder_nose * mag_vertical) if mag_shoulder_nose > 0 else 0
        head_angle = math.degrees(math.acos(max(-1, min(1, cos_angle))))
    
    # Calculate arm angles
    # Left elbow angle
    if all(k in keypoints for k in [11, 13, 15]):  # left_shoulder, left_elbow, left_wrist
        shoulder = keypoints[11][:2]
        elbow = keypoints[13][:2]
        wrist = keypoints[15][:2]
        
        arm_angles["left_elbow"] = _angle_between_points(shoulder, elbow, wrist)
    
    # Right elbow angle
    if all(k in keypoints for k in [12, 14, 16]):  # right_shoulder, right_elbow, right_wrist
        shoulder = keypoints[12][:2]
        elbow = keypoints[14][:2]
        wrist = keypoints[16][:2]
        
        arm_angles["right_elbow"] = _angle_between_points(shoulder, elbow, wrist)
    
    # Calculate leg angles
    # Left knee angle
    if all(k in keypoints for k in [23, 25, 27]):  # left_hip, left_knee, left_ankle
        hip = keypoints[23][:2]
        knee = keypoints[25][:2]
        ankle = keypoints[27][:2]
        
        leg_angles["left_knee"] = _angle_between_points(hip, knee, ankle)
    
    # Right knee angle
    if all(k in keypoints for k in [24, 26, 28]):  # right_hip, right_knee, right_ankle
        hip = keypoints[24][:2]
        knee = keypoints[26][:2]
        ankle = keypoints[28][:2]
        
        leg_angles["right_knee"] = _angle_between_points(hip, knee, ankle)
    
    # Calculate torso angle (angle between torso and horizontal)
    if all(k in keypoints for k in [11, 12, 23, 24]):  # shoulders and hips
        left_shoulder = keypoints[11][:2]
        right_shoulder = keypoints[12][:2]
        left_hip = keypoints[23][:2]
        right_hip = keypoints[24][:2]
        
        # Midpoints
        shoulder_mid = [(left_shoulder[0] + right_shoulder[0]) / 2, 
                        (left_shoulder[1] + right_shoulder[1]) / 2]
        hip_mid = [(left_hip[0] + right_hip[0]) / 2, 
                  (left_hip[1] + right_hip[1]) / 2]
        
        # Vector from hip midpoint to shoulder midpoint
        v_hip_shoulder = [shoulder_mid[0] - hip_mid[0], shoulder_mid[1] - hip_mid[1]]
        
        # Vector pointing right (horizontal)
        v_horizontal = [1, 0]
        
        # Calculate angle
        dot_product = v_hip_shoulder[0] * v_horizontal[0] + v_hip_shoulder[1] * v_horizontal[1]
        mag_hip_shoulder = math.sqrt(v_hip_shoulder[0]**2 + v_hip_shoulder[1]**2)
        mag_horizontal = 1  # Unit vector
        
        cos_angle = dot_product / (mag_hip_shoulder * mag_horizontal) if mag_hip_shoulder > 0 else 0
        torso_angle = math.degrees(math.acos(max(-1, min(1, cos_angle))))
    
    return head_angle, arm_angles, leg_angles, torso_angle


def _angle_between_points(p1: List, p2: List, p3: List) -> float:
    """
    Calculate angle between three points (p1-p2-p3).
    
    Args:
        p1, p2, p3: Points as [x, y] coordinates

    Returns:
        Angle in degrees
    """
    # Vectors
    v1 = [p1[0] - p2[0], p1[1] - p2[1]]
    v2 = [p3[0] - p2[0], p3[1] - p2[1]]
    
    # Dot product
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    
    # Magnitudes
    mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
    mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
    
    # Angle
    cos_angle = dot_product / (mag1 * mag2) if mag1 * mag2 > 0 else 0
    angle_degrees = math.degrees(math.acos(max(-1, min(1, cos_angle))))
    
    return angle_degrees


def analyze_risk(features: Dict[str, Any]) -> Tuple[str, float, List[str]]:
    """
    Analyze risk level based on posture features.
    
    Args:
        features: Dictionary of posture features

    Returns:
        Tuple containing:
        - posture_type: string describing the posture type
        - risk_score: numerical risk score (1-10)
        - reasons: list of reasons for the risk assessment
    """
    reasons = []
    risk_score = 0
    
    # Check for face down (highest risk)
    if features["face_down"]:
        posture_type = "Nguy hiểm"
        risk_score = 9.5
        reasons.append("Trẻ đang úp mặt, có nguy cơ nghẹt thở")
    
    # Check for prone position (medium-high risk)
    elif features["head_angle"] < 30:
        posture_type = "Có nguy cơ"
        risk_score = 7.5
        reasons.append("Trẻ đang nằm sấp, có thể xoay và úp mặt")
    
    # Check for side lying (medium risk)
    elif features["torso_angle"] > 45:
        posture_type = "Có nguy cơ"
        risk_score = 4.0
        reasons.append("Trẻ đang nằm nghiêng, có thể lật úp")
    
    # Otherwise, likely safe position
    else:
        posture_type = "An toàn"
        risk_score = 2.0
        reasons.append("Tư thế nằm an toàn")
    
    # Add details about limbs and blanket
    if features["blanket_kicked"]:
        reasons.append("Đạp chăn, có thể bị lạnh")
        risk_score += 0.5
    
    # Check for bent limbs
    if any(angle < 45 for angle in features["arm_angles"].values()):
        reasons.append("Tay gấp không tự nhiên")
        risk_score += 0.5
    
    if any(angle < 45 for angle in features["leg_angles"].values()):
        reasons.append("Chân gấp không tự nhiên")
        risk_score += 0.5
    
    # Ensure risk score is within bounds
    risk_score = min(max(risk_score, 1.0), 10.0)
    
    return posture_type, risk_score, reasons

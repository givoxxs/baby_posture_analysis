import numpy as np # type: ignore
from typing import Dict, List, Tuple, Any, Optional
import math

import logging # Sử dụng logging

logger = logging.getLogger(__name__)
# MediaPipe landmark indices
NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28


def calculate_vector(p1: List[float], p2: List[float]) -> List[float]:
    """Calculate vector from p1 to p2."""
    return [p2[0] - p1[0], p2[1] - p1[1]]

def calculate_angle(v1: List[float], v2: List[float]) -> float:
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    mag_v1 = math.sqrt(v1[0]**2 + v1[1]**2)
    mag_v2 = math.sqrt(v2[0]**2 + v2[1]**2)
    
    # Handle zero division
    if mag_v1 * mag_v2 == 0:
        return 0.0
        
    cos_angle = dot_product / (mag_v1 * mag_v2)
    # Clamp value to valid range for arccos
    cos_angle = max(min(cos_angle, 1.0), -1.0)
    angle_rad = math.acos(cos_angle)
    angle_deg = angle_rad * 180 / math.pi
    
    return angle_deg

def detect_face_down(keypoints: List[List[float]]) -> bool:
    # Check nose visibility
    nose_visible = keypoints[NOSE][3] > 0.5
    
    if not nose_visible:
        print("Nose not visible")
        return True
    # else: 
    #     return False
    
    # Calculate head-torso angle
    # Use average of left and right shoulders
    shoulder_x = (keypoints[LEFT_SHOULDER][0] + keypoints[RIGHT_SHOULDER][0]) / 2
    shoulder_y = (keypoints[LEFT_SHOULDER][1] + keypoints[RIGHT_SHOULDER][1]) / 2

    hip_x = (keypoints[LEFT_HIP][0] + keypoints[RIGHT_HIP][0]) / 2
    hip_y = (keypoints[LEFT_HIP][1] + keypoints[RIGHT_HIP][1]) / 2
    
    nose_x, nose_y = keypoints[NOSE][0], keypoints[NOSE][1]
    v_shoulder_nose = [nose_x - shoulder_x, nose_y - shoulder_y]
    
    # Vector from shoulder to nose
    v_shoulder_nose = [nose_x - shoulder_x, nose_y - shoulder_y]
    # Vertical vector (pointing downward in image coordinates)
    # v_vertical = [0, -1]
    v_vertical = [hip_x - shoulder_x, hip_y - shoulder_y]
    
    angle = calculate_angle(v_shoulder_nose, v_vertical)
    
    # If angle is less than 15 degrees, face is likely down
    print(f"Angle: {angle}")
    return angle < 15

def detect_blanket_kicked(keypoints: List[List[float]]) -> bool:
    """
    Detect if blanket is kicked based on visibility of lower body keypoints.
    
    Args:
        keypoints: List of keypoints [x, y, z, visibility]
    
    Returns:
        Boolean indicating if blanket is kicked
    """
    # Check visibility of hip, knee, and ankle keypoints
    # hip_visible = (keypoints[LEFT_HIP][3] > 0.5) or (keypoints[RIGHT_HIP][3] > 0.5)
    # knee_visible = (keypoints[LEFT_KNEE][3] > 0.5) or (keypoints[RIGHT_KNEE][3] > 0.5)
    # ankle_visible = (keypoints[LEFT_ANKLE][3] > 0.5) or (keypoints[RIGHT_ANKLE][3] > 0.5)
    # return hip_visible or knee_visible or ankle_visible
    lower_body_indices = [LEFT_HIP, RIGHT_HIP, LEFT_KNEE, RIGHT_KNEE, LEFT_ANKLE, RIGHT_ANKLE]
    invisible_count = 0
    for idx in lower_body_indices:
        if keypoints[idx][3] < 0.5:
            invisible_count += 1
    # If more than 3 keypoints are not visible, we assume blanket is kicked
    return invisible_count >= 3

def calculate_arm_angles(keypoints: List[List[float]]) -> Dict[str, float]:
    """
    Calculate angles of arms.
    
    Args:
        keypoints: List of keypoints [x, y, z, visibility]
    
    Returns:
        Dictionary with left and right arm angles
    """
    angles = {}
    
    # Left arm angle
    if keypoints[LEFT_SHOULDER][3] > 0.5 and keypoints[LEFT_ELBOW][3] > 0.5 and keypoints[LEFT_WRIST][3] > 0.5:
        v_shoulder_elbow = calculate_vector(
            [keypoints[LEFT_SHOULDER][0], keypoints[LEFT_SHOULDER][1]],
            [keypoints[LEFT_ELBOW][0], keypoints[LEFT_ELBOW][1]]
        )
        v_elbow_wrist = calculate_vector(
            [keypoints[LEFT_ELBOW][0], keypoints[LEFT_ELBOW][1]],
            [keypoints[LEFT_WRIST][0], keypoints[LEFT_WRIST][1]]
        )
        angles["left"] = calculate_angle(v_shoulder_elbow, v_elbow_wrist)
    else:
        angles["left"] = 180.0  # Default when not visible
    
    # Right arm angle
    if keypoints[RIGHT_SHOULDER][3] > 0.5 and keypoints[RIGHT_ELBOW][3] > 0.5 and keypoints[RIGHT_WRIST][3] > 0.5:
        v_shoulder_elbow = calculate_vector(
            [keypoints[RIGHT_SHOULDER][0], keypoints[RIGHT_SHOULDER][1]],
            [keypoints[RIGHT_ELBOW][0], keypoints[RIGHT_ELBOW][1]]
        )
        v_elbow_wrist = calculate_vector(
            [keypoints[RIGHT_ELBOW][0], keypoints[RIGHT_ELBOW][1]],
            [keypoints[RIGHT_WRIST][0], keypoints[RIGHT_WRIST][1]]
        )
        angles["right"] = calculate_angle(v_shoulder_elbow, v_elbow_wrist)
    else:
        angles["right"] = 180.0  # Default when not visible
    
    return angles

def calculate_leg_angles(keypoints: List[List[float]]) -> Dict[str, float]:
    """
    Calculate angles of legs.
    
    Args:
        keypoints: List of keypoints [x, y, z, visibility]
    
    Returns:
        Dictionary with left and right leg angles
    """
    angles = {}
    
    # Left leg angle
    if keypoints[LEFT_HIP][3] > 0.5 and keypoints[LEFT_KNEE][3] > 0.5 and keypoints[LEFT_ANKLE][3] > 0.5:
        v_hip_knee = calculate_vector(
            [keypoints[LEFT_HIP][0], keypoints[LEFT_HIP][1]],
            [keypoints[LEFT_KNEE][0], keypoints[LEFT_KNEE][1]]
        )
        v_knee_ankle = calculate_vector(
            [keypoints[LEFT_KNEE][0], keypoints[LEFT_KNEE][1]],
            [keypoints[LEFT_ANKLE][0], keypoints[LEFT_ANKLE][1]]
        )
        angles["left"] = calculate_angle(v_hip_knee, v_knee_ankle)
    else:
        angles["left"] = 180.0  # Default when not visible
    
    # Right leg angle
    if keypoints[RIGHT_HIP][3] > 0.5 and keypoints[RIGHT_KNEE][3] > 0.5 and keypoints[RIGHT_ANKLE][3] > 0.5:
        v_hip_knee = calculate_vector(
            [keypoints[RIGHT_HIP][0], keypoints[RIGHT_HIP][1]],
            [keypoints[RIGHT_KNEE][0], keypoints[RIGHT_KNEE][1]]
        )
        v_knee_ankle = calculate_vector(
            [keypoints[RIGHT_KNEE][0], keypoints[RIGHT_KNEE][1]],
            [keypoints[RIGHT_ANKLE][0], keypoints[RIGHT_ANKLE][1]]
        )
        angles["right"] = calculate_angle(v_hip_knee, v_knee_ankle)
    else:
        angles["right"] = 180.0  # Default when not visible
    
    return angles

def calculate_torso_angle(keypoints: List[List[float]]) -> float:
    """
    Calculate torso angle relative to horizontal.
    
    Args:
        keypoints: List of keypoints [x, y, z, visibility]
    
    Returns:
        Torso angle in degrees
    """
    # Use average of left and right shoulders and hips
    if (keypoints[LEFT_SHOULDER][3] > 0.5 and keypoints[RIGHT_SHOULDER][3] > 0.5 and
            keypoints[LEFT_HIP][3] > 0.5 and keypoints[RIGHT_HIP][3] > 0.5):
        
        shoulder_x = (keypoints[LEFT_SHOULDER][0] + keypoints[RIGHT_SHOULDER][0]) / 2
        shoulder_y = (keypoints[LEFT_SHOULDER][1] + keypoints[RIGHT_SHOULDER][1]) / 2
        
        hip_x = (keypoints[LEFT_HIP][0] + keypoints[RIGHT_HIP][0]) / 2
        hip_y = (keypoints[LEFT_HIP][1] + keypoints[RIGHT_HIP][1]) / 2
        
        # Vector from hip to shoulder
        v_shoulder_hip = [shoulder_x - hip_x, shoulder_y - hip_y]
        # Horizontal vector
        v_horizontal = [1, 0]
        
        angle = calculate_angle(v_shoulder_hip, v_horizontal)
        return angle
    else:
        return 0.0  # Default when not visible

def extract_posture_features(keypoints: List[List[float]]) -> Dict[str, Any]:
    """
    Extract all posture features from keypoints.
    
    Args:
        keypoints: List of keypoints [x, y, z, visibility]
    
    Returns:
        Dictionary of posture features
    """
    features = {}
    
    # Face down detection -> vie: "Trẻ đang úp mặt"
    features["face_down"] = detect_face_down(keypoints)
     
    # Blanket kicked detection -> vie: "Trẻ đạp chăn"
    features["blanket_kicked"] = detect_blanket_kicked(keypoints)
    
    # Arm angles -> vie: "Tay gấp không tự nhiên"
    features["arm_angles"] = calculate_arm_angles(keypoints)
    
    # Leg angles -> vie: "Chân gấp không tự nhiên"
    features["leg_angles"] = calculate_leg_angles(keypoints)
    
    # Torso angle -> vie: "Tư thế nằm an toàn"
    features["torso_angle"] = calculate_torso_angle(keypoints)
    
    return features

def analyze_risk(features: Dict[str, Any]) -> Tuple[str, float, List[str]]:
    """
    Analyze risk level based on posture features.
    
    Args:
        features: Dictionary of posture features
    
    Returns:
        Tuple of (posture_type, risk_score, reasons)
    """
    posture_type = "An toàn"
    risk_score = 1.0
    reasons = []
    
    # Check for face down (highest risk)
    if features["face_down"]:
        posture_type = "Nguy hiểm"
        risk_score = 8.5
        reasons.append("Trẻ đang úp mặt, nguy cơ ngạt thở")
    
    # Check for prone position (high risk)
    elif features["torso_angle"] < 15:
        posture_type = "Nguy hiểm"
        risk_score = 7.0
        reasons.append("Trẻ đang nằm sấp, có thể xoay và úp mặt")
    
    # Check for side lying (medium risk)
    elif features["torso_angle"] < 45:
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

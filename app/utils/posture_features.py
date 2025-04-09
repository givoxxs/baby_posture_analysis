import numpy as np # type: ignore
from typing import Dict, List, Tuple, Any, Optional
import math

import logging # Sử dụng logging

logger = logging.getLogger(__name__)
# MediaPipe landmark indices
NOSE = 0
LEFT_EYE_INNER = 1
LEFT_EYE = 2
LEFT_EYE_OUTER = 3
RIGHT_EYE_INNER = 4
RIGHT_EYE = 5
RIGHT_EYE_OUTER = 6
LEFT_EAR = 7
RIGHT_EAR = 8
MOUTH_LEFT = 9
MOUTH_RIGHT = 10
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_PINKY = 17
RIGHT_PINKY = 18
LEFT_INDEX = 19
RIGHT_INDEX = 20
LEFT_THUMB = 21
RIGHT_THUMB = 22
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_HEEL = 29
RIGHT_HEEL = 30
LEFT_FOOT_INDEX = 31
RIGHT_FOOT_INDEX = 32

def calculate_vector_2d(p1: List[float], p2: List[float]) -> List[float]:
    """Calculate 2D vector [x, y] from p1 to p2."""
    # Đảm bảo p1 và p2 có ít nhất 2 phần tử
    if len(p1) < 2 or len(p2) < 2:
        return [0.0, 0.0]
    return [p2[0] - p1[0], p2[1] - p1[1]]

def calculate_angle_2d(v1: List[float], v2: List[float]) -> float:
    """Calculate angle between two 2D vectors in degrees."""
    if len(v1) < 2 or len(v2) < 2: return 0.0
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    mag_v1 = math.sqrt(v1[0]**2 + v1[1]**2)
    mag_v2 = math.sqrt(v2[0]**2 + v2[1]**2)
    if mag_v1 * mag_v2 == 0: return 0.0
    cos_angle = max(min(dot_product / (mag_v1 * mag_v2), 1.0), -1.0)
    angle_rad = math.acos(cos_angle)
    return math.degrees(angle_rad)

def calculate_distance_xy(p1: List[float], p2: List[float]) -> float:
    """Calculate Euclidean distance between two points using x, y coordinates."""
    if len(p1) < 2 or len(p2) < 2: return 0.0
    return math.dist(p1[:2], p2[:2])

def get_keypoint(keypoints: List[List[float]], index: int, visibility_threshold: float = 0.4) -> Optional[List[float]]:
    """Safely get a keypoint if its index is valid and visibility is above threshold."""
    if 0 <= index < len(keypoints) and keypoints[index][3] >= visibility_threshold:
        return keypoints[index] # Trả về [x, y, z, visibility]
    return None

# --- Logic Phát hiện Đặc trưng Mới ---

def detect_face_down_v2(keypoints: List[List[float]], visibility_threshold: float = 0.4) -> bool:
    """
    Improved face down detection (Heuristic - needs validation).
    Checks visibility of facial landmarks and compares Z depth.
    """
    nose = get_keypoint(keypoints, NOSE, visibility_threshold)
    print("NOSE:", nose)
    left_eye = get_keypoint(keypoints, LEFT_EYE, visibility_threshold)
    print("LEFT_EYE:", left_eye)
    right_eye = get_keypoint(keypoints, RIGHT_EYE, visibility_threshold)
    print("RIGHT_EYE:", right_eye)
    left_ear = get_keypoint(keypoints, LEFT_EAR, visibility_threshold)
    print("LEFT_EAR:", left_ear)
    right_ear = get_keypoint(keypoints, RIGHT_EAR, visibility_threshold)
    print("RIGHT_EAR:", right_ear)
    
    if nose is None:
        logger.info("Nose not visible, suspecting face down.")
        print("Nose not visible, suspecting face down.")
        return True
    
    output = [nose, left_eye, right_eye, left_ear, right_ear]
    
    # nếu có ít nhất 4 điểm trên mặt là None -> nghi ngờ úp mặt
    invisible_count = sum(1 for point in output if point is None)
    
    if invisible_count >= 4:
        logger.info(f"Face landmarks largely invisible ({invisible_count}/5), suspecting face down.")
        print(f"Face landmarks largely invisible ({invisible_count}/5), suspecting face down.")
        return True
    
    # So sánh Z của mũi với vai (nếu mũi có Z lớn hơn đáng kể -> úp)
    print("So sánh Z của mũi với vai")
    left_shoulder = get_keypoint(keypoints, LEFT_SHOULDER, 0.3) 
    right_shoulder = get_keypoint(keypoints, RIGHT_SHOULDER, 0.3)

    if nose and left_shoulder and right_shoulder:
        shoulder_z_avg = (left_shoulder[2] + right_shoulder[2]) / 2
        print("Shoulder Z avg:", shoulder_z_avg)
        nose_z = nose[2]
        
        z_diff_threshold = 0.05 # Ví dụ ngưỡng chênh lệch Z (cần điều chỉnh!)
        if nose_z > shoulder_z_avg + z_diff_threshold:
            logger.info(f"Nose Z ({nose_z:.2f}) significantly larger than avg shoulder Z ({shoulder_z_avg:.2f}), suspecting face down.")
            print(f"Nose Z ({nose_z:.2f}) significantly larger than avg shoulder Z ({shoulder_z_avg:.2f}), suspecting face down.")
            return True

    return False

def is_likely_covered(keypoints: List[List[float]], visibility_threshold: float = 0.4, min_invisible: int = 2) -> bool:
    print("=======================")
    print("is_likely_covered")
    lower_body_indices = [LEFT_HIP, RIGHT_HIP, LEFT_KNEE, RIGHT_KNEE, LEFT_ANKLE, RIGHT_ANKLE]
    invisible_count = 0
    visible_count = 0
    for idx in lower_body_indices:
        kp = get_keypoint(keypoints, idx, visibility_threshold)
        print(f"Keypoint {idx}: {kp}")
        print(f"Keypoint {idx} visibility: {kp[3] if kp else 'N/A'}")
        if kp is None:
            if not (0 <= idx < len(keypoints)):
                invisible_count += 1
            elif keypoints[idx][3] < visibility_threshold:
                invisible_count += 1
        else:
            visible_count += 1

    # If very few points are visible, assume covered
    logger.debug(f"Lower body visibility check: Invisible={invisible_count}, Visible={visible_count}")
    print(f"Lower body visibility check: Invisible={invisible_count}, Visible={visible_count}")
    return invisible_count >= min_invisible

def calculate_arm_angles_v2(keypoints: List[List[float]], visibility_threshold: float = 0.5) -> Dict[str, Optional[float]]:
    """Calculate arm angles (elbow flexion). Returns None if angle cannot be calculated."""
    angles = {"left": None, "right": None}
    # Left arm
    ls = get_keypoint(keypoints, LEFT_SHOULDER, visibility_threshold)
    le = get_keypoint(keypoints, LEFT_ELBOW, visibility_threshold)
    lw = get_keypoint(keypoints, LEFT_WRIST, visibility_threshold)
    if ls and le and lw:
        v_shoulder_elbow = calculate_vector_2d(ls, le)
        v_elbow_wrist = calculate_vector_2d(le, lw)
        angles["left"] = calculate_angle_2d(v_shoulder_elbow, v_elbow_wrist)

    # Right arm
    rs = get_keypoint(keypoints, RIGHT_SHOULDER, visibility_threshold)
    re = get_keypoint(keypoints, RIGHT_ELBOW, visibility_threshold)
    rw = get_keypoint(keypoints, RIGHT_WRIST, visibility_threshold)
    if rs and re and rw:
        v_shoulder_elbow = calculate_vector_2d(rs, re)
        v_elbow_wrist = calculate_vector_2d(re, rw)
        angles["right"] = calculate_angle_2d(v_shoulder_elbow, v_elbow_wrist)

    return angles

def calculate_leg_angles_v2(keypoints: List[List[float]], visibility_threshold: float = 0.5) -> Dict[str, Optional[float]]:
    """Calculate leg angles (knee flexion). Returns None if angle cannot be calculated."""
    angles = {"left": None, "right": None}
    # Left leg
    lh = get_keypoint(keypoints, LEFT_HIP, visibility_threshold)
    lk = get_keypoint(keypoints, LEFT_KNEE, visibility_threshold)
    la = get_keypoint(keypoints, LEFT_ANKLE, visibility_threshold)
    if lh and lk and la:
        v_hip_knee = calculate_vector_2d(lh, lk)
        v_knee_ankle = calculate_vector_2d(lk, la)
        angles["left"] = calculate_angle_2d(v_hip_knee, v_knee_ankle)

    # Right leg
    rh = get_keypoint(keypoints, RIGHT_HIP, visibility_threshold)
    rk = get_keypoint(keypoints, RIGHT_KNEE, visibility_threshold)
    ra = get_keypoint(keypoints, RIGHT_ANKLE, visibility_threshold)
    if rh and rk and ra:
        v_hip_knee = calculate_vector_2d(rh, rk)
        v_knee_ankle = calculate_vector_2d(rk, ra)
        angles["right"] = calculate_angle_2d(v_hip_knee, v_knee_ankle)

    return angles

# --- Hàm Phân loại Tư thế Nằm Nghiêng Mới ---

def check_side_lying_indicators(
    keypoints: List[List[float]],
    vis_threshold: float = 0.4,
    z_diff_ratio_threshold: float = 0.25, # Ngưỡng chênh lệch Z chuẩn hóa
    angle_threshold_min: float = 25.0,    # Ngưỡng góc tối thiểu (độ)
    angle_threshold_max: float = 155.0   # Ngưỡng góc tối đa (độ)
) -> Tuple[bool, bool, Optional[str]]:
    print("=======================")
    print("check_side_lying_indicators")
    ls = get_keypoint(keypoints, LEFT_SHOULDER, vis_threshold)
    print("LEFT_SHOULDER:", ls)
    print("LEFT_SHOULDER visibility:", ls[3] if ls else 'N/A')
    rs = get_keypoint(keypoints, RIGHT_SHOULDER, vis_threshold)
    print("RIGHT_SHOULDER:", rs)
    print("RIGHT_SHOULDER visibility:", rs[3] if rs else 'N/A')
    lh = get_keypoint(keypoints, LEFT_HIP, vis_threshold)
    print("LEFT_HIP:", lh)
    print("LEFT_HIP visibility:", lh[3] if lh else 'N/A')
    rh = get_keypoint(keypoints, RIGHT_HIP, vis_threshold)
    print("RIGHT_HIP:", rh)
    print("RIGHT_HIP visibility:", rh[3] if rh else 'N/A')
    
    if ls[2] * rs[2] < 0 and abs(ls[2] - rs[2]) > 0.15: # Nếu Z của vai trái và phải khác dấu -> nằm nghiêng
        print("Shoulder Z difference:", ls[2], rs[2])
        return True, False # Nằm nghiêng
    
    if lh[2] * rh[2] < 0 and abs(lh[2] - rh[2]) > 0.15: # Nếu Z của hông trái và phải khác dấu -> nằm  nghiêng
        print("Hip Z difference:", lh[2], rh[2])
        return True, False # Nằm nghiêng
    
    print("Shoulder:", ls, rs)
    print("Hip:", lh, rh)

    if not (ls and rs and lh and rh):
        print("Not enough keypoints to determine side lying.")
        return False, False # Not enough info

    # 1. Check Z-difference
    # shoulder_width_xy = calculate_distance_xy(ls, rs) + 1e-6 # Epsilon for stability
    # hip_width_xy = calculate_distance_xy(lh, rh) + 1e-6
    # delta_z_shoulders = abs(ls[2] - rs[2])
    # delta_z_hips = abs(lh[2] - rh[2])
    # norm_delta_z_shoulders = delta_z_shoulders / shoulder_width_xy
    # norm_delta_z_hips = delta_z_hips / hip_width_xy
    # print('norm_delta_z_shoulders:', norm_delta_z_shoulders)
    # print('norm_delta_z_hips:', norm_delta_z_hips)
    # print('z_diff_ratio_threshold:', z_diff_ratio_threshold)
    # is_z_diff_significant = norm_delta_z_shoulders > z_diff_ratio_threshold or \
    #                         norm_delta_z_hips > z_diff_ratio_threshold
    
    # logger.debug(f"Side check Z: norm_dZ_sh={norm_delta_z_shoulders:.2f}, norm_dZ_hip={norm_delta_z_hips:.2f}, threshold={z_diff_ratio_threshold}")
    # print(f"Side check Z: norm_dZ_sh={norm_delta_z_shoulders:.2f}, norm_dZ_hip={norm_delta_z_hips:.2f}, threshold={z_diff_ratio_threshold}")
    
    # if is_z_diff_significant:
    #     print("Z difference significant, likely side lying.")
    #     return True, False # Nằm nghiêng
    
    is_likely_side = False
    is_clearly_not_side = False

    return is_likely_side, is_clearly_not_side


def classify_position_v3(keypoints: List[List[float]], vis_threshold: float = 0.4) -> str:
    """Classify main body position: supine, side_left, side_right, prone_suspicious, unknown."""

    # Check face visibility first for prone suspicion
    is_face_down = detect_face_down_v2(keypoints, vis_threshold)
    if is_face_down:
        return "prone_suspicious"

    # Check side lying indicators
    is_likely_side, is_clearly_not_side = check_side_lying_indicators(
        keypoints, 
        vis_threshold,
        z_diff_ratio_threshold=0.1
        )

    if is_likely_side:
        return "side" # Chỉ cần trả về "side" nói chung
    elif is_clearly_not_side:
        return "supine" # Assume supine if clearly not side and not prone
    else:
        return "unknown" # Ambiguous case

# --- Cập nhật Hàm Trích xuất và Phân tích ---

def extract_posture_features_v3(keypoints: List[List[float]], vis_threshold: float = 0.4) -> Dict[str, Any]:
    """
    Extract posture features using updated logic.
    """
    features = {}

    if not keypoints or len(keypoints) < 33: # Check if keypoints list is valid
         logger.warning("Invalid or insufficient keypoints received.")
         # Return default/empty features
         return {
            "position": "unknown",
            "is_covered": None, # Use None to indicate uncertainty
            "is_face_down": None,
            "arm_angles": {"left": None, "right": None},
            "leg_angles": {"left": None, "right": None},
            "unnatural_limbs": None,
            "avg_visibility": 0.0
         }

    # Phân loại tư thế chính (dùng hàm mới)
    features["position"] = classify_position_v3(keypoints, vis_threshold)

    # Kiểm tra che phủ (dùng hàm mới)
    features["is_covered"] = is_likely_covered(keypoints, vis_threshold)

    # Tính góc tay/chân (dùng hàm mới)
    features["arm_angles"] = calculate_arm_angles_v2(keypoints, vis_threshold)
    features["leg_angles"] = calculate_leg_angles_v2(keypoints, vis_threshold)

    # Kiểm tra tay/chân gấp không tự nhiên (ngưỡng ví dụ)
    unnatural = False
    arm_angles = features["arm_angles"]
    leg_angles = features["leg_angles"]
    # Check arms: angle is not None and is < 45 or > 190
    if (arm_angles["left"] is not None and (arm_angles["left"] < 30 or arm_angles["left"] > 220)) or \
       (arm_angles["right"] is not None and (arm_angles["right"] < 30 or arm_angles["right"] > 220)):
        unnatural = True
    # Check legs: angle is not None and is < 45 or > 190
    if not unnatural: # Only check legs if arms are okay
         if (leg_angles["left"] is not None and (leg_angles["left"] < 30 or leg_angles["left"] > 220)) or \
            (leg_angles["right"] is not None and (leg_angles["right"] < 30 or leg_angles["right"] > 220)):
             unnatural = True
    features["unnatural_limbs"] = unnatural

    # Tính visibility trung bình để ước lượng confidence
    valid_visibilities = [kp[3] for kp in keypoints if len(kp) > 3] # Lấy vis của tất cả điểm hợp lệ
    features["avg_visibility"] = np.mean(valid_visibilities) if valid_visibilities else 0.0

    return features

def analyze_risk_v3(features: Dict[str, Any]) -> Dict[str, Any]:
    risk_level = "Low" # Default to Low
    risk_score = 1.0   # Default score
    reasons = []
    recommendations = []

    # Lấy các features đã tính toán
    position = features.get("position", "unknown")
    is_covered = features.get("is_covered") # Can be None
    unnatural_limbs = features.get("unnatural_limbs") # Can be None
    avg_visibility = features.get("avg_visibility", 0.0)

    # --- Đánh giá Rủi ro Chính dựa trên Tư thế ---
    if position == "prone_suspicious":
        risk_level = "Critical"
        risk_score = 9.5
        reasons.append("!!! Nghi ngờ trẻ nằm sấp/úp mặt - Nguy cơ ngạt thở CAO NHẤT !!!")
        recommendations.append("!!! KIỂM TRA NGAY LẬP TỨC VÀ ĐẶT TRẺ NẰM NGỬA !!!")
    elif position in "side":
        risk_level = "Medium"
        risk_score = 4.0
        reasons.append("Trẻ nằm nghiêng - Có nguy cơ lật sang tư thế sấp.")
        recommendations.append("Theo dõi trẻ thường xuyên, đảm bảo không gian ngủ an toàn nếu trẻ tự lật.")
    elif position == "supine":
        risk_level = "Low"
        risk_score = 1.5
        reasons.append("Trẻ nằm ngửa - Tư thế ngủ an toàn nhất.")
        recommendations.append("Duy trì tư thế nằm ngửa khi ngủ.")
    elif position == "unknown":
        risk_level = "Unknown"
        risk_score = 5.0 # Score cao hơn vì không chắc chắn
        reasons.append("Không thể xác định rõ tư thế do thiếu thông tin hoặc hình ảnh không rõ ràng.")
        recommendations.append("Kiểm tra trực tiếp trẻ và đảm bảo camera quan sát tốt hơn.")
    else: # Trường hợp position không hợp lệ
        risk_level = "Error"
        risk_score = 5.0
        reasons.append("Lỗi xử lý phân loại tư thế.")
        recommendations.append("Kiểm tra lại hệ thống hoặc hình ảnh đầu vào.")

    # --- Điều chỉnh Rủi ro dựa trên Yếu tố Phụ ---
    base_risk_score = risk_score # Lưu điểm cơ bản từ tư thế

    if is_covered is True:
        reasons.append("Phần thân dưới trẻ có khả năng bị che phủ (chăn, vật cản).")
        # Chỉ tăng rủi ro nếu không phải nằm ngửa an toàn
        if position != "supine":
             risk_score += 1.5
        recommendations.append("Đảm bảo chăn/vật che không trùm lên mặt trẻ và không gây quá nóng.")
    elif is_covered is False:
        reasons.append("Trẻ không bị che phủ phần thân dưới.")
        recommendations.append("Đảm bảo nhiệt độ phòng phù hợp để trẻ không bị lạnh.")
        # Có thể giảm nhẹ điểm nếu nằm ngửa
        if position == "supine":
             risk_score = max(1.0, risk_score - 0.5)

    if unnatural_limbs is True:
        reasons.append("Tư thế tay hoặc chân có vẻ không tự nhiên (quá gập hoặc quá duỗi).")
        # Tăng rủi ro đáng kể nếu tư thế chính đã có rủi ro
        risk_score += 2.0 if base_risk_score >= 4.0 else 1.0
        recommendations.append("Kiểm tra xem tay/chân trẻ có bị kẹt, vướng hoặc khó chịu không.")

    # --- Chuẩn hóa Điểm và Mức độ Rủi ro Cuối cùng ---
    risk_score = min(max(risk_score, 1.0), 10.0) # Giới hạn điểm trong khoảng 1-10

    if risk_score >= 8.5: risk_level = "Critical"
    elif risk_score >= 6.0: risk_level = "High"
    elif risk_score >= 4.0: risk_level = "Medium"
    else: risk_level = "Low" # Bao gồm cả trường hợp Unknown nếu score thấp

    # --- Tính Confidence ---
    # Dựa vào visibility trung bình và độ chắc chắn của việc phân loại tư thế
    confidence = avg_visibility * 100
    if position == "unknown" : confidence *= 0.7 # Giảm confidence nếu không chắc chắn về tư thế
    confidence = round(max(0.0, min(confidence, 100.0)), 1)

    # --- Thêm Recommendations Chung ---
    if "KIỂM TRA NGAY LẬP TỨC" not in " ".join(recommendations): # Chỉ thêm nếu chưa có cảnh báo khẩn
         recommendations.append("Luôn đặt trẻ nằm ngửa khi cho trẻ ngủ và ngủ trưa.")
         recommendations.append("Sử dụng mặt phẳng ngủ cứng, phẳng trong giường cũi hoặc nôi đáp ứng tiêu chuẩn an toàn.")
         recommendations.append("Giữ không gian ngủ của trẻ không có chăn mềm, gối, đồ chơi hoặc các vật dụng khác.")

    return {
        "position": position, # Tư thế chính
        "is_covered": is_covered, # Có bị che phủ không (True/False/None)
        "unnatural_limbs": unnatural_limbs, # Có tay/chân không tự nhiên không (True/False/None)
        "risk_level": risk_level, # Mức độ rủi ro (Low/Medium/High/Critical/Error)
        "risk_score": round(risk_score, 1), # Điểm rủi ro (1.0-10.0)
        "confidence": confidence, # Độ tin cậy (0-100%)
        "reasons": reasons, # Danh sách lý do (có thể trống)
        "recommendations": list(dict.fromkeys(recommendations)) # Loại bỏ trùng lặp và giữ thứ tự
    }


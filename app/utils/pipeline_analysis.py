import numpy as np
import cv2
import pandas as pd
import mediapipe as mp
import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import base64
import os

from app.utils.image_helper import Image_Helper, Image_Rotation_Helper
from app.utils.keypoints_helper import KeypointsExtractorHelper
from app.utils.pose_scaler_helper import PoseScalerHelper

class BabyPostureAnalysisPipeline:
    """
    Pipeline hoàn chỉnh để phân tích tư thế em bé từ một ảnh đơn lẻ
    Với các chức năng:
    - Phát hiện tư thế nằm (ngửa, nghiêng, sấp)
    - Phát hiện mặt có bị che khuất không
    - Phát hiện trẻ có đắp chăn không
    """
    
    def __init__(self, model_path, scaler_path):
        """
        Khởi tạo pipeline
        
        Args:
            model_path: Đường dẫn đến file mô hình
            scaler_path: Đường dẫn đến file scaler
        """
        # Load mô hình và scaler
        self.model = self._load_model(model_path)
        self.scaler = self._load_model(scaler_path)
        
        # Định nghĩa các keypoints quan trọng
        self.IMPORTANT_KEYPOINTS = [
            "nose",
            "left_eye_inner",
            "left_eye",
            "left_eye_outer",
            "right_eye_inner",
            "right_eye",
            "right_eye_outer",
            "left_ear",
            "right_ear",
            "mouth_left",
            "mouth_right",
            "left_shoulder",
            "right_shoulder",
            "left_elbow",
            "right_elbow",
            "left_wrist",
            "right_wrist",
            "left_pinky",
            "right_pinky",
            "left_index",
            "right_index",
            "left_thumb",
            "right_thumb",
            "left_hip",
            "right_hip",
            "left_knee",
            "right_knee",
            "left_ankle",
            "right_ankle",
            "left_heel",
            "right_heel",
            "left_foot_index",
            "right_foot_index",
        ]

        # Map số sang tên lớp
        self.CLASS_LABELS = {
            0: 'Nằm ngửa',
            1: 'Nằm nghiêng', 
            2: 'Nằm sấp'
        }
        
        # Khởi tạo các đối tượng cần thiết cho xử lý ảnh
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Khởi tạo pose detector từ MediaPipe
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=True,
            min_detection_confidence=0.5
        )
        
        # Khởi tạo các helper
        self.image_helper = Image_Helper()
        self.image_rotation_helper = Image_Rotation_Helper()
        self.keypoints_helper = KeypointsExtractorHelper(self.IMPORTANT_KEYPOINTS, self.mp_pose)
        self.pose_scaler_helper = PoseScalerHelper(self.IMPORTANT_KEYPOINTS, self.mp_pose)
    
    def _load_model(self, file_path):
        """
        Load mô hình từ file
        
        Args:
            file_path: Đường dẫn đến file mô hình
            
        Returns:
            model: Mô hình đã được load
        """
        with open(file_path, 'rb') as file:
            model = pickle.load(file)
        return model
    
    def preprocess_image(self, image):
        """
        Tiền xử lý ảnh từ đường dẫn hoặc từ ảnh đã được đọc
        
        Args:
            image: Đường dẫn đến file ảnh hoặc ảnh đã được đọc
            
        Returns:
            image_rgb: Ảnh đã được tiền xử lý
            original_image: Ảnh gốc đã được đọc
        """
        if isinstance(image, str) or isinstance(image, Path):
            # Đọc ảnh từ đường dẫn
            original_image = cv2.imread(str(image))
        else:
            # Nếu đã là ảnh
            original_image = image.copy()
        
        # Kiểm tra xem ảnh có phải là ảnh grayscale không
        if len(original_image.shape) == 2 or original_image.shape[2] == 1:
            # Chuyển đổi grayscale sang BGR
            original_image = cv2.cvtColor(original_image, cv2.COLOR_GRAY2BGR)
        
        # Chuyển đổi ảnh sang định dạng vuông
        image_squared, new_size = self.image_helper.square_image(original_image)
        
        # Chuyển đổi ảnh sang RGB (MediaPipe yêu cầu RGB)
        image_rgb = cv2.cvtColor(image_squared, cv2.COLOR_BGR2RGB)
        
        return image_rgb, original_image, new_size
    
    def extract_keypoints(self, image):
        """
        Trích xuất keypoints từ ảnh
        
        Args:
            image: Ảnh cần trích xuất keypoints
            
        Returns:
            df_keypoints: DataFrame chứa các keypoints đã được trích xuất
            results: Kết quả trích xuất từ MediaPipe
        """
        # Xử lý ảnh với MediaPipe Pose
        results = self.pose.process(image)
        
        # Kiểm tra xem có phát hiện được pose không
        if not results.pose_landmarks:
            return None, None
        
        # Chuẩn hóa hướng của pose
        results.pose_landmarks = self.image_rotation_helper.rotate_image_baby(results.pose_landmarks)
        
        # Trích xuất và chuẩn hóa các keypoints sử dụng helper
        df_keypoints = self.keypoints_helper.process_keypoints(results.pose_landmarks.landmark)
        
        return df_keypoints, results
    
    def predict_posture(self, df_keypoints):
        """
        Dự đoán tư thế từ keypoints
        
        Args:
            df_keypoints: DataFrame chứa các keypoints
            
        Returns:
            predicted_class: Lớp dự đoán
            probabilities: Xác suất cho mỗi lớp
        """
        # Chuẩn hóa dữ liệu
        X = self.scaler.transform(df_keypoints.values.reshape(1, -1))
        
        # Dự đoán
        predicted_class = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0].tolist()
        
        return predicted_class, probabilities
    # detect_face_covering method has been removed
    
    def detect_blanket_covering(self, results, image):
        """
        Phát hiện xem trẻ có đắp chăn không dựa vào khả năng nhìn thấy các điểm keypoints trên cơ thể
        
        Args:
            results: Kết quả từ MediaPipe pose
            image: Ảnh đã được tiền xử lý
            
        Returns:
            is_covered: True nếu có đắp chăn, False nếu không
            coverage_ratio: Tỉ lệ phủ (0-1)
        """
        if not results.pose_landmarks:
            return False, 0.0
        
        #[LEFT_HIP, RIGHT_HIP, LEFT_KNEE, RIGHT_KNEE, LEFT_ANKLE, RIGHT_ANKLE]
        body_indices = [23, 24, 25, 26, 27, 28]
        
        # Đếm số điểm keypoints trên cơ thể được phát hiện
        visibility_threshold = 0.5
        visible_points = 0
        total_visibility = 0.0
        
        for idx in body_indices:
            if idx < len(results.pose_landmarks.landmark) and results.pose_landmarks.landmark[idx].visibility > visibility_threshold:
                visible_points += 1
                total_visibility += results.pose_landmarks.landmark[idx].visibility
    
        is_covered = visible_points < len(body_indices) * 0.5
        coverage_ratio = 1.0 - (total_visibility / len(body_indices) if len(body_indices) > 0 else 0.0)
        print(f"Blanket covering detected: {is_covered}, Coverage ratio: {coverage_ratio}")
    
        return is_covered, coverage_ratio
    
    def visualize_result(self, image, results, predicted_class, probabilities, face_covered, is_covered):
        """
        Hiển thị kết quả trên ảnh
        
        Args:
            image: Ảnh gốc
            results: Kết quả từ MediaPipe
            predicted_class: Lớp dự đoán
            probabilities: Xác suất cho mỗi lớp
            face_covered: True nếu mặt bị che, False nếu không
            is_covered: True nếu có đắp chăn, False nếu không
            
        Returns:
            annotated_image: Ảnh với kết quả phân tích
        """
        # Copy ảnh để vẽ trên đó
        annotated_image = image.copy()
        
        # Vẽ landmarks nếu có
        if results and results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                annotated_image,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style())
        
        # Thêm thông tin về tư thế được dự đoán
        predicted_label = self.CLASS_LABELS[predicted_class] if predicted_class is not None else "Không xác định"
        
        # Sử dụng PIL để hỗ trợ hiển thị text tiếng Việt
        from PIL import Image, ImageDraw, ImageFont
        
        # Chuyển đổi ảnh từ numpy array sang PIL Image
        pil_image = Image.fromarray(annotated_image)
        draw = ImageDraw.Draw(pil_image)
        
        # Tìm font hỗ trợ Unicode
        try:
            # Font cho Windows với kích thước nhỏ hơn
            font_large = ImageFont.truetype("arial.ttf", 20)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except IOError:
            try:
                # Font cho Linux với kích thước nhỏ hơn
                font_large = ImageFont.truetype("DejaVuSans.ttf", 20)
                font_small = ImageFont.truetype("DejaVuSans.ttf", 16)
            except IOError:
                # Fallback nếu không tìm thấy font
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
        
        # Vị trí văn bản
        y_offset = 10
        
        # Thêm viền cho text để dễ đọc hơn trên nền ảnh bất kỳ
        shadow_offset = 1
        shadow_color = (0, 0, 0)  # Đen
        text_color = (255, 255, 255)  # Trắng
        
        # Thêm text thông tin kết quả với viền
        text = f"Tư thế: {predicted_label}"
        # Vẽ viền (shadow)
        for dx, dy in [(-shadow_offset, -shadow_offset), (shadow_offset, -shadow_offset),
                      (-shadow_offset, shadow_offset), (shadow_offset, shadow_offset)]:
            draw.text((10 + dx, y_offset + dy), text, font=font_large, fill=shadow_color)
        # Vẽ text chính
        draw.text((10, y_offset), text, font=font_large, fill=text_color)
        
        # Thêm thông tin về mặt và đắp chăn
        # face_text = f"Mặt bị che: {'Có' if face_covered else 'Không'}"
        blanket_text = f"Đắp chăn: {'Có' if is_covered else 'Không'}"
        
        # Vẽ thông tin về mặt
        # y_pos = y_offset + 25
        # for dx, dy in [(-shadow_offset, -shadow_offset), (shadow_offset, -shadow_offset),
        #               (-shadow_offset, shadow_offset), (shadow_offset, shadow_offset)]:
        #     # draw.text((10 + dx, y_pos + dy), face_text, font=font_small, fill=shadow_color)
        #     draw.text((10 + dx, y_pos + dy), font=font_small, fill=shadow_color)
        # # draw.text((10, y_pos), face_text, font=font_small, fill=text_color)
        # draw.text((10, y_pos), font=font_small, fill=text_color)
        
        # Vẽ thông tin về đắp chăn
        # y_pos += 20
        y_pos = y_offset + 25
        for dx, dy in [(-shadow_offset, -shadow_offset), (shadow_offset, -shadow_offset),
                      (-shadow_offset, shadow_offset), (shadow_offset, shadow_offset)]:
            draw.text((10 + dx, y_pos + dy), blanket_text, font=font_small, fill=shadow_color)
        draw.text((10, y_pos), blanket_text, font=font_small, fill=text_color)
        
        # Thêm thông tin về xác suất cho mỗi lớp
        for i, (label, prob) in enumerate(zip(self.CLASS_LABELS.values(), probabilities)):
            confidence = f"{label}: {prob*100:.1f}%"
            y_pos = y_offset + 65 + i*20
            
            # Vẽ viền
            for dx, dy in [(-shadow_offset, -shadow_offset), (shadow_offset, -shadow_offset),
                          (-shadow_offset, shadow_offset), (shadow_offset, shadow_offset)]:
                draw.text((10 + dx, y_pos + dy), confidence, font=font_small, fill=shadow_color)
            # Vẽ text chính
            draw.text((10, y_pos), confidence, font=font_small, fill=text_color)
        
        # Chuyển đổi lại từ PIL Image sang numpy array
        annotated_image = np.array(pil_image)
        
        return annotated_image
    
    def analyze_image(self, image, timestamp=None):
        """
        Phân tích ảnh em bé và trả về kết quả phân tích tư thế đầy đủ
        
        Args:
            image: Đường dẫn đến file ảnh hoặc ảnh đã được đọc
            timestamp: Thời gian chụp ảnh (mặc định là thời gian hiện tại)
            
        Returns:
            result: Dict chứa kết quả phân tích
        """
        try:
            # Gán timestamp mặc định nếu không có
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            # Đảm bảo MediaPipe Pose instance được khởi tạo mới
            self.pose.close()
            self.pose = self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                enable_segmentation=True,
                min_detection_confidence=0.5
            )
            
            start_time = time.time()
            
            # Tiền xử lý ảnh
            image_rgb, original_image, image_dimensions = self.preprocess_image(image)
            
            # Trích xuất keypoints
            df_keypoints, results = self.extract_keypoints(image_rgb)
            
            if df_keypoints is None:
                return {
                    "success": False,
                    "message": "Không thể phát hiện tư thế trong ảnh",
                    "timestamp": timestamp,
                    "processing_time_ms": int((time.time() - start_time) * 1000),
                    "image_dimensions": {
                        "width": original_image.shape[1],
                        "height": original_image.shape[0]
                    }
                }
              # Dự đoán tư thế
            predicted_class, probabilities = self.predict_posture(df_keypoints)
            
            # Phát hiện đắp chăn (mặt bị che đã được loại bỏ)
            face_covered = False  # Default value since detect_face_covering was removed
            face_confidence = 0.0  # Default value since detect_face_covering was removed
            is_covered, coverage_ratio = self.detect_blanket_covering(results, image_rgb)
            
            # Hiển thị kết quả
            result_image = self.visualize_result(
                image_rgb, results, predicted_class, probabilities, face_covered, is_covered)
            
            # Chuyển đổi ảnh sang base64 để trả về qua API
            _, buffer = cv2.imencode('.jpg', cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR))
            annotated_image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Thời gian xử lý
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Tạo kết quả
            result = {
                "success": True,
                "timestamp": timestamp,
                "analysis": {
                    "position": self.CLASS_LABELS[predicted_class],
                    "position_id": int(predicted_class),
                    "probabilities": {
                        self.CLASS_LABELS[0]: float(probabilities[0]),
                        self.CLASS_LABELS[1]: float(probabilities[1]),
                        self.CLASS_LABELS[2]: float(probabilities[2])
                    },
                    # "face_covered": face_covered,
                    # "face_confidence": float(face_confidence),
                    "is_covered": is_covered,
                    "coverage_ratio": float(coverage_ratio)
                },
                "annotated_image": annotated_image_base64,
                "processing_time_ms": processing_time_ms,
                "image_dimensions": {
                    "width": image_rgb.shape[1],
                    "height": image_rgb.shape[0]
                }
            }
            
            return result
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return {
                "success": False,
                "message": f"Lỗi khi xử lý ảnh: {str(e)}",
                "error_details": error_details,
                "timestamp": timestamp if timestamp else datetime.now().isoformat()
            }
    
    def close(self):
        """Đóng các resources"""
        if self.pose:
            self.pose.close()

import pandas as pd
import numpy as np
import mediapipe as mp

class KeypointsExtractorHelper:
    """
    Lớp trợ giúp cho việc trích xuất và xử lý keypoints từ MediaPipe
    để sử dụng trong notebook trích xuất keypoints
    """
    def __init__(self, important_landmarks, mp_pose):
        self.important_landmarks = important_landmarks
        self.mp_pose = mp_pose
        
    def extract_and_format_keypoints(self, keypoints):
        """
        Trích xuất keypoints và định dạng chúng thành DataFrame với định dạng phù hợp
        
        Args:
            keypoints: Danh sách các điểm keypoints từ MediaPipe
            
        Returns:
            df_keypoints: DataFrame chứa các keypoints đã được định dạng đúng
        """
        # Tạo tên cột cho DataFrame (tổng cộng 99 cột - 33 keypoints x 3 tọa độ)
        columns_name = [] + [f"{landmark}_{axis}" for landmark in self.important_landmarks for axis in ["x", "y", "z"]]
        
        # Tạo mảng để chứa giá trị phẳng (flattened values)
        columns_values = []
        
        # Trích xuất các giá trị x, y, z từ mỗi keypoint và thêm vào mảng giá trị
        for id, landmark in enumerate(keypoints):
            if self.mp_pose.PoseLandmark(id).name.lower() in self.important_landmarks:
                # Thêm từng giá trị riêng biệt (x, y, z) vào mảng giá trị
                columns_values.extend([landmark.x, landmark.y, landmark.z])
                
        # Tạo DataFrame với đúng số lượng cột và giá trị
        df_keypoints = pd.DataFrame([columns_values], columns=columns_name)
        
        return df_keypoints
    
    def normalize_keypoints(self, df_keypoints):
        """
        Chuẩn hóa các keypoints bằng cách dịch chúng về tâm và co giãn về kích thước chuẩn
        
        Args:
            df_keypoints: DataFrame chứa các keypoints cần được chuẩn hóa
            
        Returns:
            df_keypoints: DataFrame chứa các keypoints đã được chuẩn hóa
        """
        # Tìm tâm của cơ thể
        center = self.find_center_of_body(df_keypoints)
        
        # Dịch các điểm về tâm của cơ thể
        distance_shifting = (0 - center[0], 0 - center[1])
        for l in self.important_landmarks:
            df_keypoints[f"{l}_x"] += distance_shifting[0]
            df_keypoints[f"{l}_y"] += distance_shifting[1]
            
        # Tính hệ số co giãn
        scale_value = self.calc_scale_value(df_keypoints)
        
        # Scale lại các điểm về kích thước chuẩn
        for l in self.important_landmarks:
            df_keypoints[f"{l}_x"] *= scale_value
            df_keypoints[f"{l}_y"] *= scale_value
        
        return df_keypoints
    
    def find_center_of_body(self, df_keypoints):
        """
        Tìm tâm của cơ thể dựa trên vị trí của hông và vai
        
        Args:
            df_keypoints: DataFrame chứa các keypoints
            
        Returns:
            center: Tọa độ tâm của cơ thể
        """
        left_hip = (df_keypoints["left_hip_x"].values[0], df_keypoints["left_hip_y"].values[0])
        right_hip = (df_keypoints["right_hip_x"].values[0], df_keypoints["right_hip_y"].values[0])
        
        center_hip = (left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2
        
        left_shoulder = (df_keypoints["left_shoulder_x"].values[0], df_keypoints["left_shoulder_y"].values[0])
        right_shoulder = (df_keypoints["right_shoulder_x"].values[0], df_keypoints["right_shoulder_y"].values[0])
        
        center_shoulder = (left_shoulder[0] + right_shoulder[0]) / 2, (left_shoulder[1] + right_shoulder[1]) / 2
        
        center = (center_hip[0] + center_shoulder[0]) / 2, (center_hip[1] + center_shoulder[1]) / 2
        return center
    
    def calc_scale_value(self, df_keypoints):
        """
        Tính hệ số co giãn để chuẩn hóa kích thước
        
        Args:
            df_keypoints: DataFrame chứa các keypoints
            
        Returns:
            scale_value: Hệ số co giãn
        """
        left_hip = (df_keypoints["left_hip_x"].values[0], df_keypoints["left_hip_y"].values[0])
        right_hip = (df_keypoints["right_hip_x"].values[0], df_keypoints["right_hip_y"].values[0])
        
        center_hip = (left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2
        
        left_shoulder = (df_keypoints["left_shoulder_x"].values[0], df_keypoints["left_shoulder_y"].values[0])
        right_shoulder = (df_keypoints["right_shoulder_x"].values[0], df_keypoints["right_shoulder_y"].values[0])
        
        center_shoulder = (left_shoulder[0] + right_shoulder[0]) / 2, (left_shoulder[1] + right_shoulder[1]) / 2
        
        # Tính khoảng cách giữa vai và hông
        distance_between_hips = np.sqrt((center_hip[0] - center_shoulder[0])**2 + (center_hip[1] - center_shoulder[1])**2)
        
        # Tính hệ số co giãn (khoảng cách giữa vai và hông sẽ được co giãn về 0.5)
        scale_value = 0.5 / distance_between_hips if distance_between_hips > 0 else 1.0
        
        return scale_value
    
    def process_keypoints(self, keypoints):
        """
        Xử lý các keypoints từ MediaPipe: trích xuất và chuẩn hóa
        
        Args:
            keypoints: Danh sách các keypoints từ MediaPipe
            
        Returns:
            df_keypoints: DataFrame chứa các keypoints đã được xử lý
        """
        # Trích xuất và định dạng keypoints
        df_keypoints = self.extract_and_format_keypoints(keypoints)
        
        # Chuẩn hóa keypoints
        df_keypoints = self.normalize_keypoints(df_keypoints)
        
        return df_keypoints

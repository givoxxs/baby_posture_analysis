import pandas as pd # type: ignore
import numpy as np
import mediapipe as mp # type: ignore

class PoseScalerHelper:
    def __init__(self, IMPORTANT_LANDMARKS, mp_pose):
        self.IMPORTANT_LANDMARKS = IMPORTANT_LANDMARKS
        self.mp_pose = mp_pose
        
    def scaler_landmarks(self, keypoints):
        columns_name = [] + [f"{landmark}_{axis}" for landmark in self.IMPORTANT_LANDMARKS for axis in ["x", "y", "z"]]
        columns_values = []
        
        for id, landmark in enumerate(keypoints):
            if self.mp_pose.PoseLandmark(id).name.lower() in self.IMPORTANT_LANDMARKS:
                columns_values.append([landmark.x, landmark.y, landmark.z])
                
        df_keypoints = pd.DataFrame([columns_values], columns=columns_name)
        
        center = self.find_center_of_babay(df_keypoints)
        
        # dịch các điểm về tâm của cơ thể
        distance_shifting = (0 - center[0], 0 - center[1])
        for l in self.IMPORTANT_LANDMARKS:
            df_keypoints[f"{l}_x"] += distance_shifting[0]
            df_keypoints[f"{l}_y"] += distance_shifting[1]
            
        scale_value = self.calc_scale_value(df_keypoints)
        
        # scale lại các điểm về kích thước chuẩn
        df_keypoints = self.scale_keypoints(df_keypoints, scale_value)
        
        return df_keypoints
            
    def find_center_of_babay(self, df_keypoints):
        left_hip = (df_keypoints["left_hip_x"], df_keypoints["left_hip_y"])
        right_hip = (df_keypoints["right_hip_x"], df_keypoints["right_hip_y"])
        
        center_hip = (left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2
        
        left_shoulder = (df_keypoints["left_shoulder_x"], df_keypoints["left_shoulder_y"])
        right_shoulder = (df_keypoints["right_shoulder_x"], df_keypoints["right_shoulder_y"])
        
        center_shoulder = (left_shoulder[0] + right_shoulder[0]) / 2, (left_shoulder[1] + right_shoulder[1]) / 2
        
        resp = (center_hip[0] + center_shoulder[0]) / 2, (center_hip[1] + center_shoulder[1]) / 2
        return resp
    
    # tính hệ số co giãn -> chuẩn hóa kích thước ảnh lại
    def calc_scale_value(self, df_keypoints):
        left_hip = (df_keypoints["left_hip_x"], df_keypoints["left_hip_y"])
        right_hip = (df_keypoints["right_hip_x"], df_keypoints["right_hip_y"])
        
        center_hip = (left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2
        
        left_shoulder = (df_keypoints["left_shoulder_x"], df_keypoints["left_shoulder_y"])
        right_shoulder = (df_keypoints["right_shoulder_x"], df_keypoints["right_shoulder_y"])
        
        center_shoulder = (left_shoulder[0] + right_shoulder[0]) / 2, (left_shoulder[1] + right_shoulder[1]) / 2
        
        # tính khoảng cách giữa vai và hông
        distance_between_hips = np.sqrt((center_hip[0] - center_shoulder[0])**2 + (center_hip[1] - center_shoulder[1])**2)
        
        # tính hệ số co giãn
        scale_value = 0.5 / distance_between_hips # điều này có nghĩa là khoảng cách giữa vai và hông sẽ được co giãn về 0.5
        
        print(f"Scale value: {scale_value}")
        
        return scale_value
    
    def scale_keypoints(self, df_keypoints, scale_value):
        for l in self.IMPORTANT_LANDMARKS:
            df_keypoints[f"{l}_x"] *= scale_value
            df_keypoints[f"{l}_y"] *= scale_value
        
        return df_keypoints
    
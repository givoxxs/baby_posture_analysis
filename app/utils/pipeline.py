import numpy as np
import cv2 # type: ignore
import pandas as pd # type: ignore
import mediapipe as mp # type: ignore
from typing import Dict, List, Tuple, Any, Optional

from app.utils.image_helper import Image_Helper, Image_Rotation_Helper
from app.utils.pose_scaler_helper import PoseScalerHelper

class BabyPoseDetectionPipeline:
    def __init__(self, model, pose_estimator, image_helper: Image_Helper):
        self.mp_pose = mp.solutions.pose
        self.IMPORTANT_LANDMARKS = [
            "nose", # 0
            "left_shoulder", # 11
            "right_shoulder", # 12
            "left_elbow", # 13
            "right_elbow", # 14
            "left_pinky", # 17
            "right_pinky", # 18
            "left_index", # 19
            "right_index", # 20
            "left_hip", # 23
            "right_hip", # 24
            "left_knee", # 25
            "right_knee", # 26
            "left_foot_index", # 31
            "right_foot_index", # 32 
        ]
        self.image_helper = Image_Helper()
        self.image_rotation_helper = Image_Rotation_Helper()
        self.pose_scaler_helper = PoseScalerHelper(self.IMPORTANT_LANDMARKS, self.mp_pose)
        
    def predict(self, image, threshold=0.7):
        with self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            smooth_landmarks=True
        ) as pose:
            image, new_size = self.image_helper.process_image(image)
            
            keypoints = pose.process(image) # => trả về keypoints
            
            if not keypoints.pose_landmarks:
                raise Exception("No pose landmarks detected")
            
            image.flags.writeable = True # nhằm để có thể vẽ lên ảnh
            
            # khôi phục màu gốc của ảnh
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            try:
                keypoints.pose_landmarks = self.image_rotation_helper.rotate_image_baby(keypoints.pose_landmarks, origin_size=new_size)
                
                df_keypoints = self.pose_scaler_helper.scaler_landmarks(keypoints.pose_landmarks)
                
                keypoints_2d = df_keypoints.values.reshape(1, -1) # Chuyển đổi thành mảng 2D
                
                
                
            except Exception as e:
                raise e

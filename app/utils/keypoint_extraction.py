import numpy as np
import cv2
import mediapipe as mp
from typing import Dict, List, Tuple, Any, Optional
import time
from app.utils.image_helper import Image_Helper, Image_Rotation_Helper
from app.utils.pose_scaler_helper import PoseScalerHelper

class PoseDetector:
    """Class for detecting human pose using MediaPipe."""
    
    def __init__(self, static_image_mode: bool = True, model_complexity: int = 2, 
                 min_detection_confidence: float = 0.2):
        """
        Initialize the MediaPipe pose detection model.
        
        Args:
            static_image_mode: Whether to treat the input images as static (not video)
            model_complexity: Model complexity (0, 1, 2)
            min_detection_confidence: Minimum confidence for detection
        """
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.mp_pose = mp.solutions.pose
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence
        )
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
    
    def detect_pose(self, image: np.ndarray) -> Tuple[Optional[Dict[str, Any]], Optional[np.ndarray]]:
        """
        Detect pose in an image and return keypoints data and annotated image.
        
        Args:
            image: Input image as numpy array
        
        Returns:
            Tuple of (keypoints data, annotated image) or (None, None) if no pose detected
        """
        # Start timer
        start_time = time.time()
        
        # Convert image to RGB for MediaPipe (if not already)
        if image.shape[2] == 3 and not np.array_equal(image[0, 0], image[0, 0, ::-1]):
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image
        
        # Process the image with MediaPipe Pose
        results = self.pose.process(rgb_image)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # in milliseconds
        
        # Check if pose detection succeeded
        if not results.pose_landmarks:
            return None, None
        
        # Extract and filter keypoints
        keypoints_data = self._extract_keypoints(results, rgb_image.shape, image)
        keypoints_data["processing_time_ms"] = processing_time
        
        # Create annotated image
        annotated_image = self._draw_landmarks(rgb_image.copy(), results)
        
        return keypoints_data, annotated_image
    
    def _extract_keypoints(self, results, image_shape, image: np.ndarray) -> Dict[str, Any]:
        """Extract keypoints from MediaPipe results."""
        keypoints = []
        h, w = image_shape[:2]
        
        # Extract landmark coordinates with visibility
        for idx, landmark in enumerate(results.pose_landmarks.landmark):
            # Convert normalized coordinates to pixel values
            x, y = int(landmark.x * w), int(landmark.y * h)
            # Store x, y, z (depth), and visibility
            keypoints.append([landmark.x, landmark.y, landmark.z, landmark.visibility])
        
        # keypoints_pose_landmarks, new_image, size = self.new_extract_keypoints(image) 
        
        # for landmark in keypoints_pose_landmarks.landmark:  
        #     # Convert normalized coordinates to pixel values
        #     x, y = int(landmark.x * size[0]), int(landmark.y * size[1])  # Fixed size[1] usage
        #     keypoints.append([landmark.x, landmark.y, landmark.z, landmark.visibility])
        
        return {
            "keypoints": keypoints,
            "image_width": w,      # Updated to use size[0]
            "image_height": h      # Updated to use size[1]
        }
    
    def _draw_landmarks(self, image: np.ndarray, results) -> np.ndarray:
        """Draw pose landmarks on the image."""
        # Draw the pose landmarks
        self.mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )
        
        return image
    
    def new_extract_keypoints(self, image: np.ndarray):
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
                
            except Exception as e:
                raise e
        
            return keypoints.pose_landmarks, image, new_size
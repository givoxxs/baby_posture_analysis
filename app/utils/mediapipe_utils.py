"""
Utility functions for MediaPipe pose detection.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import time
import math


class PoseDetector:
    """Class for detecting human pose using MediaPipe."""
    
    # MediaPipe landmark indices with semantic names
    LANDMARK_INDICES = {
        'nose': 0,
        'left_eye_inner': 1,
        'left_eye': 2,
        'left_eye_outer': 3,
        'right_eye_inner': 4,
        'right_eye': 5,
        'right_eye_outer': 6,
        'left_ear': 7,
        'right_ear': 8,
        'mouth_left': 9,
        'mouth_right': 10,
        'left_shoulder': 11,
        'right_shoulder': 12,
        'left_elbow': 13,
        'right_elbow': 14,
        'left_wrist': 15,
        'right_wrist': 16,
        'left_pinky': 17,
        'right_pinky': 18,
        'left_index': 19,
        'right_index': 20,
        'left_thumb': 21,
        'right_thumb': 22,
        'left_hip': 23,
        'right_hip': 24,
        'left_knee': 25,
        'right_knee': 26,
        'left_ankle': 27,
        'right_ankle': 28,
        'left_heel': 29,
        'right_heel': 30,
        'left_foot_index': 31,
        'right_foot_index': 32
    }
    
    # Key body parts for baby posture analysis
    KEY_BODY_PARTS = {
        'nose': 0,
        'left_shoulder': 11,
        'right_shoulder': 12,
        'left_elbow': 13,
        'right_elbow': 14,
        'left_wrist': 15,
        'right_wrist': 16,
        'left_hip': 23,
        'right_hip': 24,
        'left_knee': 25,
        'right_knee': 26,
        'left_ankle': 27,
        'right_ankle': 28
    }
    
    def __init__(
        self, 
        model_complexity: int = 2,
        static_image_mode: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        confidence_threshold: float = 0.5
    ):
        """Initialize the pose detector."""
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        self.confidence_threshold = confidence_threshold
    
    def detect_pose(self, image: np.ndarray) -> Tuple[Optional[Dict[str, Any]], Optional[np.ndarray]]:
        """
        Detect pose in an image and return keypoints data and annotated image.
        """
        # Start timer
        start_time = time.time()
        
        # Convert image to RGB for MediaPipe
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process the image with MediaPipe Pose
        results = self.pose.process(rgb_image)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # in milliseconds
        
        # Check if pose detection succeeded
        if not results.pose_landmarks:
            return None, None
        
        # Extract and filter keypoints
        keypoints_data = self._extract_keypoints(results, rgb_image.shape)
        keypoints_data["processing_time_ms"] = processing_time
        
        # Create annotated image
        annotated_image = self._draw_landmarks(rgb_image.copy(), results)
        
        # Convert back to BGR for display
        annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
        
        return keypoints_data, annotated_image
    
    def _extract_keypoints(self, results, image_shape: Tuple[int, int, int]) -> Dict[str, Any]:
        """Extract keypoints from MediaPipe results."""
        height, width, _ = image_shape
        
        # Extract landmarks
        landmarks = results.pose_landmarks.landmark
        
        keypoints = []
        for idx, (name, lm_idx) in enumerate(self.LANDMARK_INDICES.items()):
            landmark = landmarks[lm_idx]
            
            # Convert normalized coordinates to image coordinates
            x, y = int(landmark.x * width), int(landmark.y * height)
            z = landmark.z * width  # Scale Z relative to width
            visibility = landmark.visibility
            
            # Only include keypoints with visibility above threshold
            if visibility >= self.confidence_threshold or lm_idx in self.KEY_BODY_PARTS.values():
                keypoints.append({
                    "id": lm_idx,
                    "name": name,
                    "x": x,
                    "y": y,
                    "z": z,
                    "visibility": float(visibility)
                })
        
        return {"keypoints": keypoints}
    
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
    
    def get_pose_angles(self, keypoints_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate joint angles from keypoints data."""
        keypoints_dict = {kp["id"]: kp for kp in keypoints_data["keypoints"]}
        angles = {}
        
        # Calculate elbow angles
        if all(k in keypoints_dict for k in [11, 13, 15]):  # left shoulder, elbow, wrist
            angles["left_elbow"] = self._calculate_angle(
                keypoints_dict[11], keypoints_dict[13], keypoints_dict[15]
            )
            
        if all(k in keypoints_dict for k in [12, 14, 16]):  # right shoulder, elbow, wrist
            angles["right_elbow"] = self._calculate_angle(
                keypoints_dict[12], keypoints_dict[14], keypoints_dict[16]
            )
        
        # Calculate knee angles
        if all(k in keypoints_dict for k in [23, 25, 27]):  # left hip, knee, ankle
            angles["left_knee"] = self._calculate_angle(
                keypoints_dict[23], keypoints_dict[25], keypoints_dict[27]
            )
            
        if all(k in keypoints_dict for k in [24, 26, 28]):  # right hip, knee, ankle
            angles["right_knee"] = self._calculate_angle(
                keypoints_dict[24], keypoints_dict[26], keypoints_dict[28]
            )
        
        # Calculate shoulder angles
        if all(k in keypoints_dict for k in [13, 11, 23]):  # left elbow, shoulder, hip
            angles["left_shoulder"] = self._calculate_angle(
                keypoints_dict[13], keypoints_dict[11], keypoints_dict[23]
            )
            
        if all(k in keypoints_dict for k in [14, 12, 24]):  # right elbow, shoulder, hip
            angles["right_shoulder"] = self._calculate_angle(
                keypoints_dict[14], keypoints_dict[12], keypoints_dict[24]
            )
        
        # Calculate hip angles
        if all(k in keypoints_dict for k in [11, 23, 25]):  # left shoulder, hip, knee
            angles["left_hip"] = self._calculate_angle(
                keypoints_dict[11], keypoints_dict[23], keypoints_dict[25]
            )
            
        if all(k in keypoints_dict for k in [12, 24, 26]):  # right shoulder, hip, knee
            angles["right_hip"] = self._calculate_angle(
                keypoints_dict[12], keypoints_dict[24], keypoints_dict[26]
            )
        
        return angles
    
    def _calculate_angle(self, point1: Dict, point2: Dict, point3: Dict) -> float:
        """Calculate the angle between three points."""
        # Get coordinates
        x1, y1 = point1["x"], point1["y"]
        x2, y2 = point2["x"], point2["y"]
        x3, y3 = point3["x"], point3["y"]
        
        # Calculate vectors
        v1 = [x1 - x2, y1 - y2]
        v2 = [x3 - x2, y3 - y2]
        
        # Calculate dot product
        dot_product = v1[0] * v2[0] + v1[1] * v2[1]
        
        # Calculate magnitudes
        mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
        mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
        
        # Calculate angle
        cos_angle = max(-1, min(1, dot_product / (mag1 * mag2)))
        angle_radians = math.acos(cos_angle)
        angle_degrees = math.degrees(angle_radians)
        
        # Ensure angle is <= 180 degrees
        angle_degrees = angle_degrees if angle_degrees <= 180 else 360 - angle_degrees
        
        return round(angle_degrees, 2)
    
    def close(self):
        """Release resources."""
        self.pose.close()


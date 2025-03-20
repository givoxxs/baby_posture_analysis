import cv2
import mediapipe as mp
import numpy as np
from typing import List, Tuple, Union, Dict, Any, Optional
from PIL import Image  
from io import BytesIO
import time

class PoseDetector:
    """
    Class for human pose detection and keypoint extraction using MediaPipe.
    
    This class handles:
    1. Person detection in images
    2. Extracting 33 standardized keypoints
    3. Depth estimation
    4. Filtering low-confidence keypoints
    """
    
    # MediaPipe Pose landmark indices with semantic meanings
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
        static_image_mode: bool = True,
        model_complexity: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        confidence_threshold: float = 0.5
    ):
        """
        Initialize the PoseDetector with MediaPipe parameters.
        
        Args:
            static_image_mode: Whether to treat input as static images (True) or video frames (False)
            model_complexity: Model complexity (0, 1, or 2). Higher = more accurate but slower
            min_detection_confidence: Minimum confidence for person detection
            min_tracking_confidence: Minimum confidence for pose tracking
            confidence_threshold: Threshold for filtering low-confidence keypoints
        """
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.mp_pose = mp.solutions.pose
        
        # Initialize MediaPipe Pose with specified parameters
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        self.confidence_threshold = confidence_threshold
    
    def detect_pose(self, image: np.ndarray) -> Tuple[Optional[Dict[str, Any]], Optional[np.ndarray]]:
        """
        Detect human pose in an image and extract keypoints.
        
        Args:
            image: Input image as numpy array (RGB format)
            
        Returns:
            Tuple of (keypoints_data, annotated_image)
            - keypoints_data: Dictionary containing keypoints and metadata
            - annotated_image: Image with pose landmarks drawn
        """
        # Ensure image is in RGB format
        if image.shape[2] == 3 and image.dtype == np.uint8:
            rgb_image = image.copy()
            if len(image.shape) == 3 and image.shape[2] == 3:
                # Convert BGR to RGB if needed
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            raise ValueError("Image must be in RGB format with uint8 type")
        
        # Process the image with MediaPipe
        start_time = time.time()
        results = self.pose.process(rgb_image)
        processing_time = (time.time() - start_time) * 1000  # in milliseconds
        
        # Check if pose detection succeeded
        if not results.pose_landmarks:
            return None, None
        
        # Extract and filter keypoints
        keypoints_data = self._extract_keypoints(results, rgb_image.shape)
        keypoints_data['processing_time_ms'] = processing_time
        
        # Create annotated image
        annotated_image = self._draw_landmarks(rgb_image.copy(), results)
        
        return keypoints_data, annotated_image
    
    def _extract_keypoints(self, results, image_shape: Tuple[int, int, int]) -> Dict[str, Any]:
        """
        Extract keypoints from MediaPipe results and format them.
        
        Args:
            results: MediaPipe pose detection results
            image_shape: Shape of the input image (height, width, channels)
            
        Returns:
            Dictionary with keypoints data
        """
        height, width, _ = image_shape
        landmarks = results.pose_landmarks.landmark
        
        # Initialize keypoints array
        keypoints = []
        filtered_keypoints = []
        
        # Extract all 33 keypoints with their coordinates and visibility
        for idx, landmark in enumerate(landmarks):
            visibility = landmark.visibility
            confidence = visibility if visibility is not None else 0
            
            # Convert normalized coordinates to pixel values
            x = landmark.x * width
            y = landmark.y * height
            z = landmark.z * width  # Depth is relative to width for scaling
            
            keypoint = {
                'id': idx,
                'name': next((k for k, v in self.LANDMARK_INDICES.items() if v == idx), f"landmark_{idx}"),
                'x': x,
                'y': y,
                'z': z,
                'visibility': visibility,
                'confidence': confidence
            }
            keypoints.append(keypoint)
            
            # Add to filtered list if confidence is above threshold
            if confidence >= self.confidence_threshold:
                filtered_keypoints.append(keypoint)
        
        # Extract world landmarks (3D coordinates in real-world meters)
        world_landmarks = []
        if results.pose_world_landmarks:
            for idx, landmark in enumerate(results.pose_world_landmarks.landmark):
                world_landmarks.append({
                    'id': idx,
                    'name': next((k for k, v in self.LANDMARK_INDICES.items() if v == idx), f"landmark_{idx}"),
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z,
                    'visibility': landmarks[idx].visibility
                })
        
        # Create output data structure
        keypoints_data = {
            'keypoints': keypoints,
            'filtered_keypoints': filtered_keypoints,
            'world_landmarks': world_landmarks,
            'image_width': width,
            'image_height': height,
            'confidence_threshold': self.confidence_threshold,
            'detected_keypoints_count': len(filtered_keypoints),
            'total_keypoints_count': len(keypoints)
        }
        
        return keypoints_data
    
    def _draw_landmarks(self, image: np.ndarray, results) -> np.ndarray:
        """
        Draw pose landmarks on the image.
        
        Args:
            image: Input image to draw on
            results: MediaPipe pose detection results
            
        Returns:
            Image with landmarks drawn
        """
        # Draw the pose landmarks
        self.mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )
        
        return image
    
    def get_pose_angles(self, keypoints_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate joint angles from pose keypoints.
        
        Args:
            keypoints_data: Keypoints data from detect_pose
            
        Returns:
            Dictionary of joint angles in degrees
        """
        if not keypoints_data or 'keypoints' not in keypoints_data:
            return {}
        
        keypoints = {kp['id']: kp for kp in keypoints_data['keypoints']}
        angles = {}
        
        # Calculate elbow angles
        if all(idx in keypoints for idx in [11, 13, 15]):  # Left arm
            angles['left_elbow'] = self._calculate_angle(
                keypoints[11],  # left_shoulder
                keypoints[13],  # left_elbow
                keypoints[15]   # left_wrist
            )
        
        if all(idx in keypoints for idx in [12, 14, 16]):  # Right arm
            angles['right_elbow'] = self._calculate_angle(
                keypoints[12],  # right_shoulder
                keypoints[14],  # right_elbow
                keypoints[16]   # right_wrist
            )
        
        # Calculate knee angles
        if all(idx in keypoints for idx in [23, 25, 27]):  # Left leg
            angles['left_knee'] = self._calculate_angle(
                keypoints[23],  # left_hip
                keypoints[25],  # left_knee
                keypoints[27]   # left_ankle
            )
        
        if all(idx in keypoints for idx in [24, 26, 28]):  # Right leg
            angles['right_knee'] = self._calculate_angle(
                keypoints[24],  # right_hip
                keypoints[26],  # right_knee
                keypoints[28]   # right_ankle
            )
        
        # Calculate hip angles
        if all(idx in keypoints for idx in [11, 23, 25]):  # Left hip
            angles['left_hip'] = self._calculate_angle(
                keypoints[11],  # left_shoulder
                keypoints[23],  # left_hip
                keypoints[25]   # left_knee
            )
        
        if all(idx in keypoints for idx in [12, 24, 26]):  # Right hip
            angles['right_hip'] = self._calculate_angle(
                keypoints[12],  # right_shoulder
                keypoints[24],  # right_hip
                keypoints[26]   # right_knee
            )
        
        return angles
    
    def _calculate_angle(self, point1: Dict, point2: Dict, point3: Dict) -> float:
        """
        Calculate the angle between three points.
        
        Args:
            point1, point2, point3: Keypoints (point2 is the vertex)
            
        Returns:
            Angle in degrees
        """
        # Get coordinates
        x1, y1 = point1['x'], point1['y']
        x2, y2 = point2['x'], point2['y']
        x3, y3 = point3['x'], point3['y']
        
        # Calculate angle using the dot product
        angle_radians = np.arctan2(y3 - y2, x3 - x2) - np.arctan2(y1 - y2, x1 - x2)
        angle_degrees = np.abs(angle_radians * 180.0 / np.pi)
        
        # Ensure angle is between 0 and 180 degrees
        angle_degrees = angle_degrees if angle_degrees <= 180 else 360 - angle_degrees
        
        return round(angle_degrees, 2)
    
    def close(self):
        """Release resources"""
        self.pose.close()


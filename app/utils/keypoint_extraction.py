import numpy as np
import cv2
import mediapipe as mp
from typing import Dict, List, Tuple, Any, Optional
import time

class PoseDetector:
    """Class for detecting human pose using MediaPipe."""
    
    def __init__(self, static_image_mode: bool = True, model_complexity: int = 2, 
                 min_detection_confidence: float = 0.5):
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
        keypoints_data = self._extract_keypoints(results, rgb_image.shape)
        keypoints_data["processing_time_ms"] = processing_time
        
        # Create annotated image
        annotated_image = self._draw_landmarks(rgb_image.copy(), results)
        
        return keypoints_data, annotated_image
    
    def _extract_keypoints(self, results, image_shape) -> Dict[str, Any]:
        """Extract keypoints from MediaPipe results."""
        keypoints = []
        h, w = image_shape[:2]
        
        # Extract landmark coordinates with visibility
        for idx, landmark in enumerate(results.pose_landmarks.landmark):
            # Convert normalized coordinates to pixel values
            x, y = int(landmark.x * w), int(landmark.y * h)
            # Store x, y, z (depth), and visibility
            keypoints.append([landmark.x, landmark.y, landmark.z, landmark.visibility])
        
        return {
            "keypoints": keypoints,
            "image_width": w,
            "image_height": h
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

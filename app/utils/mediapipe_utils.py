"""
MediaPipe utilities for pose detection.

This module provides a wrapper around MediaPipe's pose detection functionality,
with additional methods for processing and analyzing the detected poses.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, List, Tuple, Optional, Any
import logging
import math
from app.models.schemas import Point

logger = logging.getLogger(__name__)

class PoseDetector:
    """Wrapper around MediaPipe Pose for detecting human poses in images."""
    
    # Define landmark indices for easier reference
    LANDMARK_INDICES = {
        "nose": 0,
        "left_eye_inner": 1,
        "left_eye": 2,
        "left_eye_outer": 3,
        "right_eye_inner": 4,
        "right_eye": 5,
        "right_eye_outer": 6,
        "left_ear": 7,
        "right_ear": 8,
        "mouth_left": 9,
        "mouth_right": 10,
        "left_shoulder": 11,
        "right_shoulder": 12,
        "left_elbow": 13,
        "right_elbow": 14,
        "left_wrist": 15,
        "right_wrist": 16,
        "left_pinky": 17,
        "right_pinky": 18,
        "left_index": 19,
        "right_index": 20,
        "left_thumb": 21,
        "right_thumb": 22,
        "left_hip": 23,
        "right_hip": 24,
        "left_knee": 25,
        "right_knee": 26,
        "left_ankle": 27,
        "right_ankle": 28,
        "left_heel": 29,
        "right_heel": 30,
        "left_foot_index": 31,
        "right_foot_index": 32
    }
    
    def __init__(
        self, 
        static_image_mode: bool = True,
        model_complexity: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5
    ):
        """
        Initialize the PoseDetector.
        
        Args:
            static_image_mode: Whether to process single images (True) or video (False)
            model_complexity: Model complexity (0, 1, or 2; higher is more accurate but slower)
            min_detection_confidence: Minimum confidence for person detection
            min_tracking_confidence: Minimum confidence for pose tracking
        """
        self.static_image_mode = static_image_mode
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.mp_pose = mp.solutions.pose
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        logger.info(
            f"PoseDetector initialized with: static_image_mode={static_image_mode}, "
            f"model_complexity={model_complexity}, "
            f"min_detection_confidence={min_detection_confidence}"
        )
    
    def detect(self, image: np.ndarray) -> Tuple[Dict[str, Point], Optional[np.ndarray]]:
        """
        Detect pose in an image.
        
        Args:
            image: Input RGB image
            
        Returns:
            Tuple containing:
                - Dictionary of detected landmarks
                - Annotated image (if input was RGB)
        """
        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Check if already RGB (this is a heuristic)
            if np.mean(image[:, :, 0]) < np.mean(image[:, :, 2]):
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
        else:
            logger.warning("Input image is not a 3-channel RGB image")
            image_rgb = image
        
        # Process the image
        results = self.pose.process(image_rgb)
        
        # Extract landmarks
        landmarks = {}
        if results.pose_landmarks:
            for name, idx in self.LANDMARK_INDICES.items():
                landmark = results.pose_landmarks.landmark[idx]
                landmarks[name] = Point(
                    x=landmark.x,
                    y=landmark.y,
                    z=landmark.z,
                    visibility=landmark.visibility
                )
        
        # Draw landmarks on image
        annotated_image = None
        if results.pose_landmarks:
            annotated_image = image_rgb.copy()
            self.mp_drawing.draw_landmarks(
                annotated_image,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
            )
        
        if not landmarks:
            logger.warning("No pose detected in image")
        
        return landmarks, annotated_image
    
    def calculate_angle(
        self, 
        point1: Point, 
        point2: Point, 
        point3: Point
    ) -> float:
        """
        Calculate the angle between three points.
        
        Args:
            point1: First point
            point2: Middle point (vertex)
            point3: Third point
            
        Returns:
            Angle in degrees
        """
        # Extract coordinates
        a = np.array([point1.x, point1.y])
        b = np.array([point2.x, point2.y])
        c = np.array([point3.x, point3.y])
        
        # Calculate vectors
        ba = a - b
        bc = c - b
        
        # Calculate angle using dot product
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        
        return np.degrees(angle)
    
    def calculate_vector(self, point1: Point, point2: Point) -> np.ndarray:
        """
        Calculate the vector between two points.
        
        Args:
            point1: Start point
            point2: End point
            
        Returns:
            Vector as numpy array [x, y, z]
        """
        return np.array([
            point2.x - point1.x,
            point2.y - point1.y,
            point2.z - point1.z if (point1.z is not None and point2.z is not None) else 0
        ])
    
    def normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """
        Normalize a vector to unit length.
        
        Args:
            vector: Input vector
            
        Returns:
            Normalized vector
        """
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm
    
    def calculate_distance(self, point1: Point, point2: Point) -> float:
        """
        Calculate the Euclidean distance between two points.
        
        Args:
            point1: First point
            point2: Second point
            
        Returns:
            Distance between the points
        """
        return np.linalg.norm([
            point2.x - point1.x,
            point2.y - point1.y,
            (point2.z - point1.z) if (point1.z is not None and point2.z is not None) else 0
        ])
    
    def estimate_ground_plane(self, landmarks: Dict[str, Point]) -> np.ndarray:
        """
        Estimate the ground plane based on foot and ankle landmarks.
        
        Args:
            landmarks: Dictionary of landmarks
            
        Returns:
            Normal vector of the estimated ground plane
        """
        # Use ankles and feet to estimate the ground plane
        points = []
        for key in ["left_ankle", "right_ankle", "left_heel", "right_heel", 
                   "left_foot_index", "right_foot_index"]:
            if key in landmarks and landmarks[key].visibility > 0.5:
                points.append([
                    landmarks[key].x,
                    landmarks[key].y,
                    landmarks[key].z if landmarks[key].z is not None else 0
                ])
        
        if len(points) < 3:
            # Not enough points, assume default ground plane (y-axis as normal)
            return np.array([0, 1, 0])
        
        # Fit a plane to the points using least squares
        points = np.array(points)
        centroid = np.mean(points, axis=0)
        points_centered = points - centroid
        
        # SVD to find the normal vector
        _, _, vh = np.linalg.svd(points_centered)
        normal = vh[2, :]
        
        # Ensure the normal points upward
        if normal[1] < 0:
            normal = -normal
        
        return normal / np.linalg.norm(normal)


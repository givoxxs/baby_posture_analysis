"""Pose detection utility for extracting keypoints."""

import cv2
import mediapipe as mp
import numpy as np
from typing import Tuple, List, Optional, Any

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Create a Pose object for detecting poses
pose = mp_pose.Pose(
    static_image_mode=True,
    model_complexity=2,
    enable_segmentation=False,
    min_detection_confidence=0.5
)

async def detect_pose(image: np.ndarray) -> Tuple[List[List[float]], np.ndarray]:
    """
    Detect pose keypoints in the given image.
    
    Args:
        image: Input image as numpy array
        
    Returns:
        Tuple of (keypoints list, annotated image)
    """
    # Convert the BGR image to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Process the image with MediaPipe Pose
    results = pose.process(image_rgb)
    
    # Create a copy of the image for annotation
    annotated_image = image.copy()
    
    # Initialize an empty list for keypoints
    keypoints = []
    
    if results.pose_landmarks:
        # Draw the pose landmarks on the image
        mp_drawing.draw_landmarks(
            annotated_image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
        )
        
        # Extract keypoints with visibility
        for idx, landmark in enumerate(results.pose_landmarks.landmark):
            keypoints.append([landmark.x, landmark.y, landmark.z, landmark.visibility])
    
    return keypoints, annotated_image

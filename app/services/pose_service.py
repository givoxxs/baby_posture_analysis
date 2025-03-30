"""
Service for pose detection operations.
"""

import cv2
import numpy as np
import base64
import time
from fastapi import UploadFile
from typing import Dict, Any, List, Optional, Tuple

from app.utils.image_utils import load_image, to_base64
from app.utils.mediapipe_utils import PoseDetector
from app.config import settings


class PoseService:
    """Service for handling pose detection."""
    
    def __init__(self):
        """Initialize the pose service with a PoseDetector."""
        self.pose_detector = PoseDetector(
            model_complexity=settings.MODEL_COMPLEXITY,
            min_detection_confidence=settings.MIN_DETECTION_CONFIDENCE
        )
        
    async def detect_pose(
        self, 
        file: UploadFile,
        high_resolution: bool = False,
        include_annotated_image: bool = True,
        include_analysis: bool = False
    ) -> Dict[str, Any]:
        """Detect pose from an uploaded image."""
        start_time = time.time()
        
        # Load image
        image = await load_image(file)
        
        # Process image for pose detection
        if high_resolution:
            # Use higher resolution for better accuracy
            processed_image = cv2.resize(image, (1280, 720), interpolation=cv2.INTER_AREA)
        else:
            # Use standard resolution
            processed_image = cv2.resize(image, (settings.IMAGE_WIDTH, settings.IMAGE_HEIGHT), interpolation=cv2.INTER_AREA)
        
        # Detect pose
        keypoints_data, annotated_image = self.pose_detector.detect_pose(processed_image)
        
        if keypoints_data is None:
            return {"message": "No person detected in the image", "keypoints_data": {"keypoints": [], "processing_time_ms": 0, "total_processing_time_ms": 0}}
        
        # Calculate joint angles
        joint_angles = self.pose_detector.get_pose_angles(keypoints_data)
        keypoints_data["joint_angles"] = joint_angles
        
        # Create response
        total_time = (time.time() - start_time) * 1000  # in milliseconds
        keypoints_data["total_processing_time_ms"] = total_time
        
        response = {
            "keypoints_data": keypoints_data,
            "message": "Pose detected successfully"
        }
        
        # Include annotated image if requested
        if include_annotated_image and annotated_image is not None:
            response["annotated_image"] = to_base64(annotated_image)
            
        # Include posture analysis if requested
        if include_analysis:
            from app.services.posture_service import PostureService
            posture_service = PostureService()
            posture_analysis = posture_service.analyze_from_keypoints(keypoints_data)
            response["posture_analysis"] = posture_analysis
        
        return response

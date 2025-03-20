import time
import numpy as np
import cv2
from fastapi import UploadFile, HTTPException
from typing import Dict, Any, Tuple, Optional, List, Union

from app.utils.mediapipe_utils import PoseDetector
from app.utils.image_preprocessor import ImagePreProcessor
from app.services.image_service import ImageService

class PoseService:
    """Service for pose detection and analysis"""
    
    def __init__(
        self, 
        image_service: Optional[ImageService] = None,
        pose_detector: Optional[PoseDetector] = None
    ):
        """
        Initialize the pose service
        
        Args:
            image_service: Optional ImageService instance. If None, a default one is created.
            pose_detector: Optional PoseDetector instance. If None, a default one is created.
        """
        self.image_service = image_service or ImageService()
        self.pose_detector = pose_detector or PoseDetector(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            confidence_threshold=0.5
        )
    
    async def detect_pose_from_file(
        self, 
        file: UploadFile,
        high_resolution: bool = False,
        include_annotated_image: bool = True
    ) -> Dict[str, Any]:
        """
        Process an image file and detect pose
        
        Args:
            file: UploadFile from FastAPI
            high_resolution: Whether to use higher resolution for detection
            include_annotated_image: Whether to include the annotated image in the response
            
        Returns:
            Dictionary with keypoints data and optionally the annotated image
        """
        start_time = time.time()
        
        # First, preprocess the image using the image service
        await self.image_service.validate_image_file(file)
        
        # Use specialized preprocessing for MediaPipe
        processed_image = await self.image_service.processor.preprocess_for_mediapipe(
            file,
            high_resolution=high_resolution
        )
        
        # Detect pose in the processed image
        keypoints_data, annotated_image = self.pose_detector.detect_pose(processed_image)
        
        if not keypoints_data:
            raise HTTPException(
                status_code=400, 
                detail="No pose detected in the image. Please try with a different image."
            )
        
        # Calculate joint angles
        angles = self.pose_detector.get_pose_angles(keypoints_data)
        keypoints_data['joint_angles'] = angles
        
        # Calculate total processing time
        total_processing_time = (time.time() - start_time) * 1000
        keypoints_data['total_processing_time_ms'] = round(total_processing_time, 2)
        
        # Prepare response
        response = {
            "message": "Pose detection successful",
            "keypoints_data": keypoints_data,
        }
        
        # Include the annotated image if requested
        if include_annotated_image and annotated_image is not None:
            base64_annotated = self.image_service.processor.to_base64(annotated_image)
            response["annotated_image"] = base64_annotated
        
        return response
    
    async def detect_pose_from_processed_image(
        self,
        image: np.ndarray,
        include_annotated_image: bool = True
    ) -> Dict[str, Any]:
        """
        Detect pose from an already processed image
        
        Args:
            image: Preprocessed image as numpy array
            include_annotated_image: Whether to include the annotated image in the response
            
        Returns:
            Dictionary with keypoints data and optionally the annotated image
        """
        start_time = time.time()
        
        # Detect pose in the processed image
        keypoints_data, annotated_image = self.pose_detector.detect_pose(image)
        
        if not keypoints_data:
            raise HTTPException(
                status_code=400, 
                detail="No pose detected in the image. Please try with a different image."
            )
        
        # Calculate joint angles
        angles = self.pose_detector.get_pose_angles(keypoints_data)
        keypoints_data['joint_angles'] = angles
        
        # Calculate total processing time
        total_processing_time = (time.time() - start_time) * 1000
        keypoints_data['total_processing_time_ms'] = round(total_processing_time, 2)
        
        # Prepare response
        response = {
            "message": "Pose detection successful",
            "keypoints_data": keypoints_data,
        }
        
        # Include the annotated image if requested
        if include_annotated_image and annotated_image is not None:
            base64_annotated = self.image_service.processor.to_base64(annotated_image)
            response["annotated_image"] = base64_annotated
        
        return response
    
    def analyze_posture(self, keypoints_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the posture based on keypoints
        
        Args:
            keypoints_data: Keypoints data from detect_pose
            
        Returns:
            Dictionary with posture analysis results
        """
        # This is a placeholder for future implementation of posture analysis
        # Will be expanded in future with more sophisticated analysis
        
        angles = keypoints_data.get('joint_angles', {})
        
        # Basic analysis based on joint angles
        analysis = {
            "posture_type": "unknown",
            "symmetry_score": 0,
            "notes": []
        }
        
        # Check for limb symmetry (if both sides are detected)
        if 'left_knee' in angles and 'right_knee' in angles:
            knee_diff = abs(angles['left_knee'] - angles['right_knee'])
            if knee_diff > 15:
                analysis["notes"].append(f"Asymmetric knee angles (difference of {knee_diff:.1f} degrees)")
        
        if 'left_elbow' in angles and 'right_elbow' in angles:
            elbow_diff = abs(angles['left_elbow'] - angles['right_elbow'])
            if elbow_diff > 15:
                analysis["notes"].append(f"Asymmetric elbow angles (difference of {elbow_diff:.1f} degrees)")
        
        # Calculate basic symmetry score
        symmetry_deductions = 0
        if 'left_knee' in angles and 'right_knee' in angles:
            symmetry_deductions += abs(angles['left_knee'] - angles['right_knee']) / 180.0
        
        if 'left_elbow' in angles and 'right_elbow' in angles:
            symmetry_deductions += abs(angles['left_elbow'] - angles['right_elbow']) / 180.0
        
        if 'left_hip' in angles and 'right_hip' in angles:
            symmetry_deductions += abs(angles['left_hip'] - angles['right_hip']) / 180.0
        
        # Scale to 0-100
        if symmetry_deductions > 0:
            analysis["symmetry_score"] = max(0, 100 - (symmetry_deductions * 50))
        else:
            analysis["symmetry_score"] = 100
        
        analysis["symmetry_score"] = round(analysis["symmetry_score"], 1)
        
        return analysis

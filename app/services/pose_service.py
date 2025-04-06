"""
Service for pose detection operations.
"""

from fastapi import UploadFile
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import cv2
import traceback
import time

from app.utils.image_preprocessing import preprocess_image, image_to_base64, load_image
from app.utils.keypoint_extraction import PoseDetector
from app.utils.posture_features import extract_posture_features, analyze_risk

pose_detector = PoseDetector()
def get_pose_detector() -> PoseDetector:
    return pose_detector

class PoseService:
    """Service for detecting and analyzing body pose."""
    
    def __init__(self):
        # Initialize the pose detector
        self.pose_detector = get_pose_detector()
    
    async def detect_pose(
        self,
        file: UploadFile,
        include_annotated_image: bool = True,
        include_analysis: bool = False
    ) -> Dict[str, Any]:
        # Start timing
        start_time = time.time()
        
        # Preprocess the image
        # preprocessed_image = await preprocess_image(
        #     image_source=file
        # )
        preprocessed_image = await load_image(file)
        
        # Detect pose
        keypoints_data, annotated_image = self.pose_detector.detect_pose(preprocessed_image)
        
        # If no pose was detected
        if keypoints_data is None:
            return {
                "success": False,
                "message": "No pose detected in the image"
            }
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # ms
        keypoints_data["processing_time_ms"] = processing_time
        
        # Prepare response
        result = {
            "success": True,
            "keypoints": keypoints_data["keypoints"],
            "processing_time_ms": keypoints_data["processing_time_ms"]
        }
        
        # Add annotated image if requested
        if include_annotated_image and annotated_image is not None:
            result["annotated_image"] = image_to_base64(annotated_image)
        
        # Add analysis if requested
        if include_analysis:
            # Extract features from keypoints
            features = extract_posture_features(keypoints_data["keypoints"])
            
            # Analyze risk
            posture_type, risk_score, reasons = analyze_risk(features)
            
            # Add analysis to result
            result["analysis"] = {
                "posture_type": posture_type,
                "risk_score": risk_score,
                "reasons": reasons,
                "features": features
            }
        
        return result

    async def analyze_posture(
        self,
        file: UploadFile
    ) -> Dict[str, Any]:

        # Get pose detection with analysis
        result = await self.detect_pose(
            file=file,
            include_annotated_image=True,
            include_analysis=True
        )
        
        if not result["success"]:
            return result
        
        # Simplify result structure for client
        analysis = result["analysis"]
        return {
            "success": True,
            "posture_type": analysis["posture_type"],
            "risk_score": analysis["risk_score"],
            "reasons": analysis["reasons"],
            "annotated_image": result.get("annotated_image"),
            "processing_time_ms": result["processing_time_ms"]
        }
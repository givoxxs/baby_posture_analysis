"""
Service for pose detection operations.
"""

from fastapi import UploadFile
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import cv2
import traceback
import time
import logging

from app.utils.image_preprocessing import preprocess_image, image_to_base64, load_image, process_image_2
from app.utils.keypoint_extraction import PoseDetector
from app.utils.posture_features import  extract_posture_features_v3, analyze_risk_v3 #extract_posture_features, analyze_risk,

logger = logging.getLogger(__name__)

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
        
        # preprocessed_image = await load_image(file)
        
        preprocessed_image = await process_image_2(
            image_source=file
        )
        
        # Detect pose
        keypoints_data, annotated_image = self.pose_detector.detect_pose(preprocessed_image)
        
        # If no pose was detected
        if keypoints_data is None:
            return {
                "success": False,
                "message": "No pose detected in the image"
            }
        
        # Prepare response
        result = {
            "success": True,
            "keypoints": keypoints_data["keypoints"],
            "processing_time_ms": keypoints_data["processing_time_ms"],
            "image_dimensions": {
                    "width": keypoints_data.get("image_width"),
                    "height": keypoints_data.get("image_height")
                },
        }
        
        # Add annotated image if requested
        if include_annotated_image and annotated_image is not None:
            result["annotated_image"] = image_to_base64(annotated_image)
        
        # Add analysis if requested
        if include_analysis:
            features = extract_posture_features_v3(keypoints_data["keypoints"])

            result["analysis"] = analyze_risk_v3(features)

        processing_time = (time.time() - start_time) * 1000  # ms
        keypoints_data["analyze_time_ms"] = processing_time
        logger.info(f"Pose detection completed for {file.filename} in {processing_time} ms")    
        
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

        if not result.get("success"):
            logger.warning(f"Analysis failed because detection failed for {file.filename}. Message: {result.get('message')}")
            return result
        
        if "analysis" not in result:
             logger.error(f"Analysis results missing in successful detection for {file.filename}")
             return {"success": False, "message": "Analysis results are missing unexpectedly."}
        
        logger.info(f"Full analysis successful for {file.filename}")
        # print(result)
        return result
    
# TẠO INSTANCE DUY NHẤT CỦA PoseService
pose_service_instance = PoseService()
print(f"--- Đã tạo PoseService Singleton (ID: {id(pose_service_instance)}) ---")

# HÀM GETTER CHO SINGLETON
def get_singleton_pose_service() -> PoseService:
    """Trả về instance PoseService đã được tạo sẵn."""
    print(f"--- Cung cấp PoseService Singleton (ID: {id(pose_service_instance)}) ---")
    return pose_service_instance
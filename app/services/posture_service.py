"""Service for posture analysis and feature extraction."""

import numpy as np
from typing import Dict, Any, List, Tuple
import cv2
import logging

from app.utils.feature_extraction.feature_constructor import PostureFeatureConstructor
from app.utils.detect import detect_pose

logger = logging.getLogger(__name__)

class PostureService:
    """Service for analyzing baby postures from images."""
    
    def __init__(self):
        """Initialize the posture service."""
        self.feature_constructor = PostureFeatureConstructor()
        
    async def process_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Process an image to extract posture features.
        
        Args:
            image_data: Binary image data
            
        Returns:
            Dictionary containing pose keypoints and extracted features
        """
        try:
            # Convert image bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Failed to decode image")
            
            # Extract keypoints using the detection module
            keypoints, annotated_image = await detect_pose(image)
            
            if keypoints is None or len(keypoints) == 0:
                return {
                    "success": False,
                    "message": "No pose keypoints detected in the image",
                    "keypoints": None,
                    "features": None
                }
            
            # Convert keypoints to numpy array if not already
            keypoints_array = np.array(keypoints)
            
            # Construct posture features
            features = self.feature_constructor.construct_features(keypoints_array)
            
            # Encode the annotated image to return
            _, encoded_image = cv2.imencode('.jpg', annotated_image)
            annotated_image_bytes = encoded_image.tobytes()
            
            return {
                "success": True,
                "message": "Posture features extracted successfully",
                "keypoints": keypoints,
                "features": features,
                "annotated_image": annotated_image_bytes
            }
            
        except Exception as e:
            logger.error(f"Error processing image for posture analysis: {str(e)}")
            return {
                "success": False,
                "message": f"Error processing image: {str(e)}",
                "keypoints": None,
                "features": None
            }
    
    def analyze_posture(self, keypoints: List[List[float]]) -> Dict[str, Any]:
        """
        Analyze posture from existing keypoints.
        
        Args:
            keypoints: List of keypoint coordinates [x, y, z, visibility]
            
        Returns:
            Dictionary containing extracted posture features
        """
        try:
            # Convert keypoints to numpy array
            keypoints_array = np.array(keypoints)
            
            # Construct posture features
            features = self.feature_constructor.construct_features(keypoints_array)
            
            return {
                "success": True,
                "message": "Posture features extracted successfully",
                "features": features
            }
            
        except Exception as e:
            logger.error(f"Error analyzing posture from keypoints: {str(e)}")
            return {
                "success": False,
                "message": f"Error analyzing posture: {str(e)}",
                "features": None
            }
    
    def interpret_posture(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret the extracted posture features to determine baby's posture.
        
        Args:
            features: Dictionary of posture features
            
        Returns:
            Dictionary with posture interpretation
        """
        # Extract key features
        angular_features = features.get('angular_features', {})
        distance_features = features.get('distance_features', {})
        face_occlusion = features.get('face_occlusion', {})
        blanket_kick = features.get('blanket_kick', {})
        
        # Initialize interpretation result
        interpretation = {
            "posture_type": "unknown",
            "confidence": 0.0,
            "details": {}
        }
        
        # Check for face-down posture
        if 'nose_to_bed_distance' in distance_features:
            nose_to_bed = distance_features['nose_to_bed_distance']
            if nose_to_bed < 0.2:  # Nose close to bed
                interpretation["posture_type"] = "face_down"
                interpretation["confidence"] = 1.0 - (nose_to_bed / 0.2)
                interpretation["details"]["face_down"] = True
        
        # Check for side-lying posture
        if 'shoulder_horizontal_angle' in angular_features:
            shoulder_angle = angular_features['shoulder_horizontal_angle']
            if 45 < shoulder_angle < 135:  # Shoulders approximately vertical
                interpretation["posture_type"] = "side_lying"
                interpretation["confidence"] = max(0, min(1.0, (shoulder_angle - 45) / 45))
                interpretation["details"]["side_lying"] = True
        
        # Check for face occlusion
        if face_occlusion.get('face_occluded', False):
            interpretation["details"]["face_occluded"] = True
            interpretation["details"]["occlusion_confidence"] = face_occlusion.get('occlusion_confidence', 0.0)
        
        # Check for blanket kicking
        if blanket_kick.get('blanket_kicked', False):
            interpretation["details"]["blanket_kicked"] = True
            interpretation["details"]["kick_confidence"] = blanket_kick.get('kick_confidence', 0.0)
        
        # Check for arm/leg bending
        if 'left_arm_bend' in angular_features and 'right_arm_bend' in angular_features:
            left_arm_bend = angular_features['left_arm_bend']
            right_arm_bend = angular_features['right_arm_bend']
            if left_arm_bend > 90 or right_arm_bend > 90:
                interpretation["details"]["arms_bent"] = True
        
        if 'left_leg_bend' in angular_features and 'right_leg_bend' in angular_features:
            left_leg_bend = angular_features['left_leg_bend']
            right_leg_bend = angular_features['right_leg_bend']
            if left_leg_bend > 90 or right_leg_bend > 90:
                interpretation["details"]["legs_bent"] = True
        
        return interpretation

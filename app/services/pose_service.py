"""
Pose detection and analysis service.

This service integrates all components of the baby posture analysis system:
- Image processing
- Pose detection
- Feature extraction
- Posture classification
- Risk analysis
- Alert generation
"""

import cv2
import numpy as np
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from fastapi import UploadFile
import logging
import asyncio

from app.config import settings
from app.services.image_service import ImageService
from app.utils.mediapipe_utils import PoseDetector
from app.utils.image_processing import preprocess_image
from app.utils.posture_features import PostureFeatureExtractor
from app.utils.posture_classifier import PostureClassifier
from app.utils.risk_analyzer import RiskAnalyzer
from app.utils.alert_system import AlertSystem
from app.models.analysis import PoseAnalysisRecord
from app.repositories.factory import get_analysis_repository

logger = logging.getLogger(__name__)

class PoseService:
    """
    Service for detecting and analyzing baby postures in images.
    
    This service integrates the complete pipeline from image preprocessing
    through pose detection, feature extraction, classification, risk analysis,
    and alert generation.
    """
    
    def __init__(
        self,
        image_service: ImageService,
        pose_detector: PoseDetector
    ):
        """
        Initialize the pose service with required dependencies.
        
        Args:
            image_service: Service for image operations
            pose_detector: MediaPipe pose detector wrapper
        """
        self.image_service = image_service
        self.pose_detector = pose_detector
        self.feature_extractor = PostureFeatureExtractor(pose_detector)
        self.classifier = PostureClassifier()
        self.risk_analyzer = RiskAnalyzer()
        self.alert_system = AlertSystem()
        
    async def process_image(
        self,
        file: UploadFile,
        high_resolution: bool = False,
        include_annotated_image: bool = True,
        include_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Process an uploaded image to detect and analyze baby posture.
        
        Args:
            file: Uploaded image file
            high_resolution: Whether to use high resolution processing
            include_annotated_image: Whether to include annotated image in response
            include_analysis: Whether to include detailed posture analysis
            
        Returns:
            Analysis results including landmarks, posture type, risk level, etc.
        """
        # Read and validate the image
        image_data = await file.read()
        image_array = self.image_service.decode_image(image_data)
        if image_array is None:
            raise ValueError("Invalid image data")
        
        # Process the image
        return await self.analyze_image(
            image_array,
            high_resolution=high_resolution,
            include_annotated_image=include_annotated_image,
            include_analysis=include_analysis,
            filename=file.filename
        )
    
    async def analyze_image(
        self,
        image: np.ndarray,
        high_resolution: bool = False,
        include_annotated_image: bool = True,
        include_analysis: bool = True,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze an image to detect and analyze baby posture.
        
        Args:
            image: Image as numpy array
            high_resolution: Whether to use high resolution processing
            include_annotated_image: Whether to include annotated image in response
            include_analysis: Whether to include detailed posture analysis
            filename: Original filename if available
            
        Returns:
            Analysis results including landmarks, posture type, risk level, etc.
        """
        # Preprocess the image
        target_size = (640, 480) if high_resolution else (256, 256)
        preprocessed = preprocess_image(image, target_size=target_size)
        
        # Detect pose landmarks
        landmarks, annotated_image = self.pose_detector.detect(preprocessed)
        
        if not landmarks:
            logger.warning("No pose detected in image")
            return {"landmarks": {}, "pose_type": "unknown"}
        
        # Extract features from landmarks
        features = self.feature_extractor.extract_features(landmarks)
        
        # Classify posture based on features
        pose_type, confidence, classification_details = self.classifier.classify(features)
        
        # Initialize result dictionary with landmarks and pose type
        result = {
            "landmarks": landmarks,
            "pose_type": pose_type,
            "confidence": confidence
        }
        
        # Perform risk analysis if requested
        if include_analysis:
            risk_level, risk_score, analysis = self.risk_analyzer.analyze_risk(
                pose_type, confidence, features
            )
            
            result.update({
                "risk_level": risk_level,
                "risk_score": risk_score,
                "analysis": analysis
            })
            
            # Process for alerts if risk score is high enough
            alert_info = await self.alert_system.process_analysis(
                pose_type=pose_type,
                risk_level=risk_level,
                risk_score=risk_score,
                analysis=analysis,
                image_path=None  # Will be updated after saving image
            )
            
            if alert_info:
                result["alert"] = alert_info
        
        # Save annotated image if requested
        image_url = None
        if include_annotated_image and annotated_image is not None:
            # Generate unique filename
            unique_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            ext = "jpg"
            if filename:
                name_parts = os.path.splitext(filename)
                if len(name_parts) > 1:
                    ext = name_parts[1].lstrip(".")
            
            save_filename = f"pose_{timestamp}_{unique_id}.{ext}"
            save_path = os.path.join(str(settings.PROCESSED_DIR), save_filename)
            
            # Save the image
            cv2.imwrite(save_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
            
            # Generate URL path for the image
            image_url = f"/static/processed_images/{save_filename}"
            result["image_url"] = image_url
            
            # Update alert image path if alert was generated
            if "alert" in result:
                result["alert"]["image_path"] = image_url
                await self.alert_system.save_alert(result["alert"])
        
        # Store the analysis record asynchronously
        if include_analysis:
            asyncio.create_task(self._store_analysis_record(
                pose_type=pose_type,
                risk_level=result.get("risk_level"),
                risk_score=result.get("risk_score"),
                analysis=result.get("analysis"),
                landmarks=landmarks,
                original_filename=filename,
                annotated_image_path=image_url
            ))
            
        return result
    
    async def _store_analysis_record(
        self,
        pose_type: str,
        risk_level: Optional[str] = None,
        risk_score: Optional[float] = None,
        analysis: Optional[Dict[str, Any]] = None,
        landmarks: Optional[Dict[str, Any]] = None,
        original_filename: Optional[str] = None,
        annotated_image_path: Optional[str] = None
    ):
        """
        Store analysis record in the repository.
        
        Args:
            pose_type: Detected pose type
            risk_level: Risk level
            risk_score: Risk score
            analysis: Detailed analysis
            landmarks: Detected landmarks
            original_filename: Original image filename
            annotated_image_path: Path to saved annotated image
        """
        try:
            record = PoseAnalysisRecord(
                timestamp=datetime.now(),
                pose_type=pose_type,
                risk_level=risk_level,
                risk_score=risk_score,
                analysis=analysis,
                image_path=original_filename,
                annotated_image_path=annotated_image_path,
                landmarks=landmarks
            )
            
            # Convert to dict for storage
            repository = get_analysis_repository()
            await repository.save(record.dict())
            
            logger.debug(f"Stored analysis record for {pose_type} pose")
        except Exception as e:
            logger.error(f"Failed to store analysis record: {str(e)}")

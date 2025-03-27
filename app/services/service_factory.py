"""
Factory for creating service instances.

This module implements the Service Locator and Singleton patterns to manage
service instances across the application. It ensures proper initialization
and reuse of expensive resources like the MediaPipe pose detector.
"""

from typing import Dict, Any, Optional
from functools import lru_cache
import os
import logging

from app.services.image_service import ImageService
from app.services.pose_service import PoseService
from app.utils.mediapipe_utils import PoseDetector

logger = logging.getLogger(__name__)

class ServiceFactory:
    """Factory class for creating and managing service instances."""
    
    _instances: Dict[str, Any] = {}
    
    @classmethod
    def get_image_service(cls) -> ImageService:
        """
        Get or create an instance of ImageService.
        
        Returns:
            A shared ImageService instance.
        """
        if "image_service" not in cls._instances:
            logger.debug("Creating new ImageService instance")
            cls._instances["image_service"] = ImageService()
        return cls._instances["image_service"]
    
    @classmethod
    def get_pose_detector(cls, 
                         static_image_mode: bool = True, 
                         model_complexity: Optional[int] = None, 
                         min_detection_confidence: Optional[float] = None) -> PoseDetector:
        """
        Get or create an instance of PoseDetector with specified parameters.
        
        Args:
            static_image_mode: Whether to process single images (True) or video (False)
            model_complexity: Model complexity (0, 1, or 2; higher is more accurate but slower)
            min_detection_confidence: Minimum confidence for person detection
            
        Returns:
            A PoseDetector instance with the specified configuration.
        """
        # Use environment variables as defaults if not provided
        if model_complexity is None:
            model_complexity = int(os.getenv("MODEL_COMPLEXITY", "2"))
        
        if min_detection_confidence is None:
            min_detection_confidence = float(os.getenv("MIN_DETECTION_CONFIDENCE", "0.5"))
        
        # Create a unique key for this configuration
        key = f"pose_detector_{static_image_mode}_{model_complexity}_{min_detection_confidence}"
        
        if key not in cls._instances:
            logger.debug(f"Creating new PoseDetector instance with complexity={model_complexity}, "
                         f"confidence={min_detection_confidence}")
            cls._instances[key] = PoseDetector(
                static_image_mode=static_image_mode,
                model_complexity=model_complexity,
                min_detection_confidence=min_detection_confidence
            )
        
        return cls._instances[key]
    
    @classmethod
    def get_pose_service(cls) -> PoseService:
        """
        Get or create an instance of PoseService.
        
        Returns:
            A shared PoseService instance initialized with default dependencies.
        """
        if "pose_service" not in cls._instances:
            logger.debug("Creating new PoseService instance")
            image_service = cls.get_image_service()
            pose_detector = cls.get_pose_detector()
            cls._instances["pose_service"] = PoseService(
                image_service=image_service, 
                pose_detector=pose_detector
            )
        
        return cls._instances["pose_service"]
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset all instances (useful for testing or reconfiguration).
        
        This will force new instances to be created on next access.
        """
        logger.debug("Resetting all service instances")
        cls._instances = {}


# Dependency injection functions for FastAPI
@lru_cache()
def get_image_service() -> ImageService:
    """
    Dependency for getting the image service instance.
    
    This function is designed to be used with FastAPI's dependency injection system.
    
    Returns:
        A shared ImageService instance.
    """
    return ServiceFactory.get_image_service()


@lru_cache()
def get_pose_detector() -> PoseDetector:
    """
    Dependency for getting the pose detector instance.
    
    This function is designed to be used with FastAPI's dependency injection system.
    
    Returns:
        A shared PoseDetector instance with default configuration.
    """
    return ServiceFactory.get_pose_detector()


@lru_cache()
def get_pose_service() -> PoseService:
    """
    Dependency for getting the pose service instance.
    
    This function is designed to be used with FastAPI's dependency injection system.
    
    Returns:
        A shared PoseService instance.
    """
    return ServiceFactory.get_pose_service()

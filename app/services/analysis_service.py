from fastapi import UploadFile, HTTPException # type: ignore
import cv2
import numpy as np
from datetime import datetime
import os
from pathlib import Path
from typing import Dict, Any, Optional
import time
import traceback
import logging
import json
from PIL import Image
import io

from app.utils.pipeline_analysis import BabyPostureAnalysisPipeline

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service class for the baby posture analysis pipeline"""
    
    def __init__(self, model_path: str, scaler_path: str):
        """
        Initialize the analysis service
        
        Args:
            model_path: Path to the model file
            scaler_path: Path to the scaler file
        """
        self.pipeline = BabyPostureAnalysisPipeline(
            model_path=model_path,
            scaler_path=scaler_path
        )
        
    async def analyze_image(self, file: UploadFile, timestamp: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a baby posture image
        
        Args:
            file: The uploaded image file
            timestamp: Optional timestamp for the image (ISO format)
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Set default timestamp if none provided
            if timestamp is None:
                timestamp = datetime.now().isoformat()
                
            start_time = time.time()
            
            # Read image from UploadFile
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error(f"Failed to decode image: {file.filename}")
                return {
                    "success": False,
                    "message": "Failed to decode image. Please upload a valid image file.",
                    "timestamp": timestamp
                }
                
            # Analyze the image using our pipeline
            result = self.pipeline.analyze_image(image, timestamp)
            
            # Calculate total processing time including file reading
            total_processing_time = int((time.time() - start_time) * 1000)
            if result["success"]:
                result["processing_time_ms"] = total_processing_time
            
            return result
        
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Error analyzing baby posture: {str(e)}\n{error_details}")
            return {
                "success": False,
                "message": f"Error analyzing image: {str(e)}",
                "timestamp": timestamp if timestamp else datetime.now().isoformat()
            }
    
    def close(self):
        """Close resources"""
        if hasattr(self, 'pipeline'):
            self.pipeline.close()


# Singleton instance for the service
_analysis_service_instance = None

def get_singleton_analysis_service():
    """
    Get or create a singleton instance of the AnalysisService
    
    Returns:
        AnalysisService: The singleton instance
    """
    global _analysis_service_instance
    
    if _analysis_service_instance is None:
        # Determine paths based on the project structure
        base_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = base_path / 'models' / 'random_forest.pkl'
        scaler_path = base_path / 'models' / 'input_scaler.pkl'
        
        if not model_path.exists() or not scaler_path.exists():
            raise FileNotFoundError(f"Model or scaler file not found. Looked at: {model_path} and {scaler_path}")
        
        _analysis_service_instance = AnalysisService(
            model_path=str(model_path),
            scaler_path=str(scaler_path)
        )
        
    return _analysis_service_instance

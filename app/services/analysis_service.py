from fastapi import UploadFile, HTTPException  # type: ignore
import cv2
import numpy as np
from datetime import datetime
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
import time
import traceback
import logging
import json
from PIL import Image
import io
import base64
import uuid
from dotenv import load_dotenv

from app.utils.pipeline_analysis import BabyPostureAnalysisPipeline

load_dotenv()

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
            model_path=model_path, scaler_path=scaler_path
        )

    async def analyze_image(
        self, file: UploadFile, timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a baby posture image from either UploadFile or base64 string

        Args:
            input_data: Either UploadFile object or base64 string of the image
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

            # Handle different input types
            if image is None:
                logger.error(f"Failed to decode image: {file.filename}")
                return {
                    "success": False,
                    "message": "Failed to decode image. Please upload a valid image file.",
                    "timestamp": timestamp,
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
                "timestamp": timestamp if timestamp else datetime.now().isoformat(),
            }

    async def analyze_image_base64(
        self, input_data: Union[UploadFile, str], timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a baby posture image from either UploadFile or base64 string

        Args:
            input_data: Either UploadFile object or base64 string of the image
            timestamp: Optional timestamp for the image (ISO format)

        Returns:
            Dict containing analysis results
        """
        try:
            # Set default timestamp if none provided
            if timestamp is None:
                timestamp = datetime.now().isoformat()

            start_time = time.time()

            # Handle different input types
            if isinstance(input_data, UploadFile):
                # Handle UploadFile
                contents = await input_data.read()
                nparr = np.frombuffer(contents, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                filename = input_data.filename
            else:
                # Handle base64 string
                try:
                    # Remove header if present (e.g., "data:image/jpeg;base64,")
                    if "base64," in input_data:
                        base64_string = input_data.split("base64,")[1]
                    else:
                        base64_string = input_data

                    # Decode base64 to image
                    img_data = base64.b64decode(base64_string)
                    nparr = np.frombuffer(img_data, np.uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    # Generate a unique filename for the base64 image
                    filename = f"base64_image_{uuid.uuid4()}.jpg"
                except Exception as e:
                    logger.error(f"Failed to decode base64 image: {str(e)}")
                    return {
                        "success": False,
                        "message": "Failed to decode base64 image. Please provide a valid base64 encoded image.",
                        "timestamp": timestamp,
                    }

            if image is None:
                logger.error(f"Failed to decode image: {filename}")
                return {
                    "success": False,
                    "message": "Failed to decode image. Please upload a valid image file.",
                    "timestamp": timestamp,
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
                "timestamp": timestamp if timestamp else datetime.now().isoformat(),
            }

    def close(self):
        """Close resources"""
        if hasattr(self, "pipeline"):
            self.pipeline.close()


# Singleton instance for the service
_analysis_service_instance = None


def get_singleton_analysis_service():
    global _analysis_service_instance

    if _analysis_service_instance is None:
        # Get correct project root directory
        base_path = Path(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )

        # Get paths from environment
        model_path_env = os.getenv("MODEL_PATH", "app/models/random_forest.pkl")
        scaler_path_env = os.getenv("SCALER_PATH", "app/models/input_scaler.pkl")

        logger.info(f"MODEL_PATH: {model_path_env}")
        logger.info(f"SCALER_PATH: {scaler_path_env}")

        # Always combine with base_path for relative paths
        model_path = base_path / model_path_env
        scaler_path = base_path / scaler_path_env

        logger.info(f"Looking for model at: {model_path}")
        logger.info(f"Looking for scaler at: {scaler_path}")

        if not model_path.exists() or not scaler_path.exists():
            raise FileNotFoundError(
                f"Model or scaler file not found. Looked at: {model_path} and {scaler_path}"
            )

        _analysis_service_instance = AnalysisService(
            model_path=str(model_path), scaler_path=str(scaler_path)
        )

    return _analysis_service_instance

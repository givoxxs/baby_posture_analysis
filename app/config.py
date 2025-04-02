"""
Simple application configuration without complex functions.
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file explicitly before initializing settings
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    # Server settings
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    RELOAD_ON_CHANGE: bool = False
    
    # API configuration
    API_VERSION: str = "1.0.0"
    API_TITLE: str = "Baby Posture Analysis API"
    API_DESCRIPTION: str = "API for baby posture analysis using MediaPipe"
    
    # Application configuration
    DEBUG: bool = False
    RATE_LIMIT_PER_MINUTE: int = 200

    # Logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # MediaPipe configuration
    MODEL_COMPLEXITY: int = 2
    MIN_DETECTION_CONFIDENCE: float = 0.5
    MIN_TRACKING_CONFIDENCE: float = 0.5
    
    # Image processing
    IMAGE_WIDTH: int = 640
    IMAGE_HEIGHT: int = 480
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,gif"
    
    # Video processing
    FPS: int = 2
    TIME_THRESHOLD: int = 30
    
    # ML model settings
    MODEL_PATH: str = "./models/posture_model.pkl"
    CONFIDENCE_THRESHOLD: float = 0.75
    
    # Paths
    UPLOAD_DIR: str = "./uploads"
    PROCESSED_DIR: str = "./processed"
    STATIC_DIR: str = "./static"
    TEMPLATES_DIR: str = "./templates"
    
    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    # Optional fields
    LOG_FILE: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'  # Allow extra fields in the environment
    )

# Initialize the Settings instance
try:
    settings = Settings()
    # Set the log file path after initialization
    settings.LOG_FILE = os.path.join(settings.LOG_DIR, "app.log")
except Exception as e:
    print(f"Error loading settings: {e}")
    # Fallback to default settings if there's an error
    settings = Settings()
    settings.LOG_FILE = "./logs/app.log"

def create_directories():
    """Create necessary directories for the application."""
    dirs = [
        settings.UPLOAD_DIR, 
        settings.PROCESSED_DIR,
        settings.STATIC_DIR,
        settings.TEMPLATES_DIR,
        settings.LOG_DIR,
        os.path.dirname(os.path.abspath(settings.MODEL_PATH))
    ]
    
    for directory in dirs:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create directory {directory}: {e}")
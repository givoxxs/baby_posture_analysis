"""
Application configuration.

This module centralizes all configuration settings for the application, loaded from
environment variables with sensible defaults.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    RELOAD_ON_CHANGE: bool = False
    APP_VERSION: str = "1.0.0"
    
    # CORS settings - Use raw string to avoid automatic JSON parsing
    CORS_ORIGINS_STR: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    
    # MediaPipe settings
    MODEL_COMPLEXITY: int = 2
    MIN_DETECTION_CONFIDENCE: float = 0.5
    
    # Image processing settings
    IMAGE_WIDTH: int = 256
    IMAGE_HEIGHT: int = 256
    
    # Posture analysis settings
    ALERT_THRESHOLD: float = 7.0
    
    # Notification settings
    ENABLE_PUSH_NOTIFICATIONS: bool = False
    ENABLE_SMS_ALERTS: bool = False
    ENABLE_EMAIL_ALERTS: bool = False
    
    # File paths
    STATIC_DIR: Path = BASE_DIR / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    UPLOADS_DIR: Path = BASE_DIR / "static" / "uploads"
    PROCESSED_DIR: Path = BASE_DIR / "static" / "processed_images"
    DATA_DIR: Path = PROJECT_DIR / "data"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_DIR: Path = PROJECT_DIR / "logs"
    LOG_FILE: str = str(LOG_DIR / "app.log")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse CORS_ORIGINS_STR string to list when needed."""
        if not self.CORS_ORIGINS_STR or not self.CORS_ORIGINS_STR.strip():
            return ["http://localhost:3000"]
            
        # Try JSON parsing if it looks like a JSON array
        if self.CORS_ORIGINS_STR.strip().startswith("[") and self.CORS_ORIGINS_STR.strip().endswith("]"):
            try:
                parsed = json.loads(self.CORS_ORIGINS_STR)
                if isinstance(parsed, list):
                    return [str(origin) for origin in parsed if origin]
            except Exception:
                # Fall through to comma-separated handling
                pass
        
        # Handle as comma separated string
        return [i.strip() for i in self.CORS_ORIGINS_STR.split(",") if i.strip()]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create required directories
        for directory in [self.STATIC_DIR, self.TEMPLATES_DIR, self.UPLOADS_DIR, 
                          self.PROCESSED_DIR, self.LOG_DIR, self.DATA_DIR]:
            directory.mkdir(parents=True, exist_ok=True)


# Create a global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings.
    
    This function can be used with FastAPI's dependency injection system.
    
    Returns:
        The application settings instance.
    """
    return settings

"""
Simple application configuration without complex functions.
"""

import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
STATIC_DIR = PROJECT_DIR / "static"
TEMPLATES_DIR = PROJECT_DIR / "templates"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    RELOAD_ON_CHANGE: bool = False
    APP_VERSION: str = "1.0.0"
    
    # CORS settings
    CORS_ORIGINS: str = Field(default="http://localhost:3000")
    
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
    
    # File paths
    STATIC_DIR: Path = STATIC_DIR
    TEMPLATES_DIR: Path = TEMPLATES_DIR
    UPLOADS_DIR: Path = STATIC_DIR / "uploads"
    PROCESSED_DIR: Path = STATIC_DIR / "processed"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_DIR: Path = PROJECT_DIR / "logs"
    LOG_FILE: str = str(LOG_DIR / "app.log")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


# Create a global settings instance
settings = Settings()


def get_settings():
    """Dependency for FastAPI to get settings."""
    return settings


# Create required directories
def create_directories():
    """Create required directories for the application."""
    directories = [
        settings.STATIC_DIR,
        settings.TEMPLATES_DIR,
        settings.UPLOADS_DIR,
        settings.PROCESSED_DIR,
        settings.LOG_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Create directories when module is imported
create_directories()

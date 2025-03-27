"""
Startup script for the Baby Posture Analysis API.

This script sets up and runs the FastAPI application.
"""

import os
import sys
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent
sys.path.append(str(project_dir))

# Import and run the app
from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    
    print(f"Starting Baby Posture Analysis API on {settings.API_HOST}:{settings.API_PORT}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Documentation available at: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    
    uvicorn.run(
        "app.main:app", 
        host=settings.API_HOST, 
        port=settings.API_PORT, 
        reload=settings.RELOAD_ON_CHANGE or settings.DEBUG
    )

"""
Application entry point for FastAPI.
"""

import os
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Load environment variables first - this is now done in config.py
# Import app settings
from app.config import settings, create_directories

# Ensure directories exist
create_directories()

# Configure logging
try:
    # Create log directory if it doesn't exist
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.FileHandler(settings.LOG_FILE),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
except Exception as e:
    print(f"Warning: Could not configure logging: {e}")
    # Fallback to basic logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning(f"Using fallback logging configuration due to error: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    debug=settings.DEBUG
)

# Configure CORS
try:
    origins = settings.CORS_ORIGINS.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS configured with origins: {origins}")
except Exception as e:
    logger.error(f"Failed to configure CORS: {e}")

# Import API endpoints
try:
    from app.api.endpoints import image, pose, posture
    
    # Register routes
    app.include_router(image.router)
    app.include_router(pose.router)
    app.include_router(posture.router)
    logger.info("API routes registered successfully")
except ImportError as e:
    logger.error(f"Failed to import API endpoints: {e}")
    # We could add a basic error route here to indicate the app is not fully functional

# Configure templates
try:
    templates_dir = Path(settings.TEMPLATES_DIR)
    if templates_dir.exists():
        templates = Jinja2Templates(directory=str(templates_dir))
        logger.info(f"Templates configured from {templates_dir}")
    else:
        logger.warning(f"Templates directory {templates_dir} does not exist")
        # Create a basic templates directory with an index.html
        templates_dir.mkdir(parents=True, exist_ok=True)
        index_html = templates_dir / "index.html"
        with open(index_html, "w") as f:
            f.write("<html><body><h1>Baby Posture Analysis API</h1><p>API is running.</p></body></html>")
        templates = Jinja2Templates(directory=str(templates_dir))
except Exception as e:
    logger.error(f"Failed to configure templates: {e}")
    # Define a minimal template handler for the root route

# Mount static files
try:
    static_dir = Path(settings.STATIC_DIR)
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"Static files mounted from {static_dir}")
    else:
        logger.warning(f"Static directory {static_dir} does not exist")
        # Create a basic static directory
        static_dir.mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.error(f"Failed to mount static files: {e}")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render main page."""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Failed to render index template: {e}")
        return HTMLResponse("<html><body><h1>Baby Posture Analysis API</h1><p>API is running but templates are not configured correctly.</p></body></html>")

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy", 
        "version": settings.API_VERSION,
        "debug_mode": settings.DEBUG
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "127.0.0.1")
    reload_on_change = os.getenv("RELOAD_ON_CHANGE", "false").lower() == "true"
    
    logger.info(f"Starting application on {host}:{port} (reload={reload_on_change})")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload_on_change)
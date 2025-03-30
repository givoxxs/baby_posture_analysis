"""
Application entry point for FastAPI.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging

from app.config import settings, create_directories

# Ensure directories exist
create_directories()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Baby Posture Analysis API",
    description="API for analyzing baby sleeping postures",
    version=settings.APP_VERSION,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure templates
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

# Import API endpoints
from app.api.endpoints import image, pose, posture

# Register routes
app.include_router(image.router)
app.include_router(pose.router)
app.include_router(posture.router)

# Mount static files
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render main page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": settings.APP_VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.RELOAD_ON_CHANGE)
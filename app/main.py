"""Main FastAPI application module."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Ensure directories exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Configure application
app = FastAPI(
    title="Baby Posture Analysis API",
    description="API for analyzing baby sleeping postures",
    version="1.0.0",
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Configure templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Import routers after FastAPI instance creation
from app.routers import image, pose, posture  # Removed 'detect' from the import

# Register routes
app.include_router(image.router)
app.include_router(pose.router)
app.include_router(posture.router)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/preprocess_image", response_class=HTMLResponse)
async def preprocess_image(request: Request):
    """Render image preprocessing page"""
    return templates.TemplateResponse("index_2.html", {"request": request})

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("API_PORT", 8000)), reload=True)
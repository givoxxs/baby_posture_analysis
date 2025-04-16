"""
Application entry point for FastAPI.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.api import image, pose, pipeline

# Create FastAPI app
app = FastAPI(
    title="Baby Posture Analysis",
    description="API for analyzing baby posture from images",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(image.router)
app.include_router(pose.router)
app.include_router(pipeline.router)

# Create static directory if it does n't exist
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Root endpoint - serve the HTML file
@app.get("/")
async def read_index():
    return FileResponse("app/templates/index.html")
"""
Application entry point for FastAPI.
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from pyngrok import ngrok # type: ignore

load_dotenv()

ngrok.set_auth_token(os.getenv("NGROK_AUTHTOKEN"))
public_url = ngrok.connect(8080)
print(f"Public URL: {public_url}")

from app.api import analyze, video_analyze
from app.services.websocket_service import WebSocketHandler

# Ensure logs directory exists
logs_dir = Path("logs")
if not logs_dir.exists():
    logs_dir.mkdir(parents=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(logs_dir / "app.log",  encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("app.main")
logger.info("Logging configured successfully")

# Initialize WebSocket handler
websocket_handler = WebSocketHandler()

# Create FastAPI app
app = FastAPI(
    title="Baby Posture Analysis",
    description="API for analyzing baby posture from images and videos",
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

app.include_router(analyze.router)
app.include_router(video_analyze.router)

# Log API routes registration
logger.info("API routes registered successfully")

# Create static directory if it does n't exist
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    
# Root endpoint - serve the HTML file
@app.get("/")
async def read_index():
    return FileResponse("app/templates/index.html")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket_handler.handle_connection(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

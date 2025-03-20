from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import os
import traceback
import time
from dotenv import load_dotenv

from app.utils.image_utils import ImagePreProcessor

# Load environment variables
load_dotenv()

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure templates directory exists
TEMPLATES_DIR.mkdir(exist_ok=True)

# Create templates instance
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app = FastAPI(
    title="Baby Posture Analysis API",
    description="API for analyzing baby posture from images",
    version="1.0.0"
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory if it exists
static_dir = Path(BASE_DIR, "static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Dependency to get the image processor
def get_image_processor():
    return ImagePreProcessor(width=640, height=480)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index_2.html", {"request": request})

@app.get("/index_2", response_class=HTMLResponse)
async def get_upload_page(request: Request):
    """
    Render the image upload and processing page
    """
    return templates.TemplateResponse("index_2.html", {"request": request})

@app.post("/api/images/process-upload")
async def process_uploaded_image(
    file: UploadFile = File(...),
    apply_resize: bool = Form(True),
    apply_normalize: bool = Form(True),
    apply_filter: bool = Form(True),
    filter_type: str = Form("gaussian"),
    processor: ImagePreProcessor = Depends(get_image_processor)
):
    """
    Process an uploaded image file
    """
    try:
        print(f"Received file: {file.filename}, type: {file.content_type}")
        start_time = time.time()
        
        # Verify file is an image
        content_type = file.content_type
        if not content_type or not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"File must be an image, got {content_type}")
            
        # Process the image
        processed_image = await processor.preprocess_image(
            file,
            apply_resize=apply_resize,
            apply_normalize=apply_normalize,
            apply_filter=apply_filter,
            filter_type=filter_type
        )
        
        # Convert processed image to base64
        base64_image = processor.to_base64(processed_image)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            "message": "Image processed successfully",
            "processed_image": base64_image,
            "width": processor.width,
            "height": processor.height,
            "processing_time_ms": round(processing_time, 2)
        }
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error processing image: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/api/images/process-mediapipe")
async def process_for_mediapipe(
    file: UploadFile = File(...),
    high_resolution: bool = Form(False),
    processor: ImagePreProcessor = Depends(get_image_processor)
):
    """
    Process an uploaded image with optimizations for MediaPipe
    """
    try:
        print(f"Received file for MediaPipe: {file.filename}, type: {file.content_type}")
        start_time = time.time()
        
        # Verify file is an image
        content_type = file.content_type
        if not content_type or not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"File must be an image, got {content_type}")
            
        # Process the image with MediaPipe optimizations
        processed_image = await processor.preprocess_for_mediapipe(
            file,
            high_resolution=high_resolution
        )
        
        # Convert processed image to base64
        base64_image = processor.to_base64(processed_image)
        
        # Get dimensions
        width = 1280 if high_resolution else processor.width
        height = 720 if high_resolution else processor.height
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            "message": "Image processed for MediaPipe successfully",
            "processed_image": base64_image,
            "width": width,
            "height": height,
            "processing_time_ms": round(processing_time, 2)
        }
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error processing image for MediaPipe: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Error processing image for MediaPipe: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("API_PORT", 8000)), reload=True)
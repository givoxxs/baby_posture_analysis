import os
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load environment variables
load_dotenv()

# Import routers
from app.routers import image

app = FastAPI(
    title="Baby Posture Analysis API",
    description="API for analyzing baby posture from images",
    version="1.0.0"
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Register routers
app.include_router(image.router)

@app.get("/", include_in_schema=False)
async def root():
    from fastapi.responses import FileResponse
    return FileResponse("app/static/index.html")

@app.get("/test")
async def read_root():
    return {"message": "Welcome to Baby Posture Detection API"}

@app.post("/detect_posture")
async def detect_posture(data: dict):
    return {"status": "Posture detection logic not implemented yet."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("API_PORT", 8000)), reload=True)
import os
from tempfile import template
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Baby Posture Detection API",
    description="API for detecting baby postures using MediaPipe",
    version="1.0.0"
)

# CORS setup
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API routes
# app.include_router(api_router, prefix="/api")

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
"""
Main FastAPI application module.

This module initializes and configures the FastAPI application instance,
sets up middleware, logging, and registers routes and error handlers.
"""

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import sys
import logging
import logging.config
import time

# Import settings first so directories are created
from app.config import settings, get_settings

# Configure logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(extra)s"
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "app.utils.log_filters.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": settings.LOG_FILE,
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
        }
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "file"],
            "level": settings.LOG_LEVEL,
            "propagate": True
        },
        "uvicorn": {
            "handlers": ["console", "file"],
            "level": settings.LOG_LEVEL,
            "propagate": False
        },
        "fastapi": {
            "handlers": ["console", "file"],
            "level": settings.LOG_LEVEL,
            "propagate": False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Configure application
app = FastAPI(
    title="Baby Posture Analysis API",
    description="API for analyzing baby sleeping postures for safety monitoring",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,  # Disable redoc in production
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if not settings.DEBUG else ["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header showing request processing time."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Configure templates
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

# Import error handlers
from app.utils.error_handling import (
    app_exception_handler, 
    http_exception_handler, 
    validation_exception_handler, 
    general_exception_handler,
    AppException
)

# Register error handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Import routers after FastAPI instance creation
from app.routers import image, pose, posture, analysis

# Register routes
app.include_router(image.router)
app.include_router(pose.router)
app.include_router(posture.router)
app.include_router(analysis.router)

# Mount static files
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, settings=Depends(get_settings)):
    """
    Render main page with the demo UI.
    
    Args:
        request: The FastAPI request object
        settings: Application settings injected by FastAPI
        
    Returns:
        HTMLResponse with the rendered index template
    """
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "app_version": settings.APP_VERSION}
    )

@app.get("/index_2", response_class=HTMLResponse)
async def get_index2(request: Request):
    """
    Render alternative UI template.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        HTMLResponse with the rendered index_2 template
    """
    return templates.TemplateResponse("index_2.html", {"request": request})

@app.get("/preprocess_image", response_class=HTMLResponse)
async def preprocess_image(request: Request):
    """
    Render image preprocessing page.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        HTMLResponse with the rendered preprocessing template
    """
    return templates.TemplateResponse("index_2.html", {"request": request})

@app.get("/health")
async def health_check(settings=Depends(get_settings)):
    """
    Health check endpoint for monitoring.
    
    Returns:
        JSON object with health status and version information
    """
    return {
        "status": "healthy", 
        "version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG
    }

logger.info(f"Application startup complete - version {settings.APP_VERSION}")

# Run the application when script is executed directly
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.API_HOST}:{settings.API_PORT} "
                f"(reload={settings.RELOAD_ON_CHANGE})")
    
    uvicorn.run(
        "app.main:app", 
        host=settings.API_HOST, 
        port=settings.API_PORT, 
        reload=settings.RELOAD_ON_CHANGE or settings.DEBUG,
        log_config=LOGGING_CONFIG
    )
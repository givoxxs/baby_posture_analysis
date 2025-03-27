"""Centralized error handling utilities for consistent API responses."""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from typing import Callable, Dict, Any, Optional
import logging
import functools

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base exception for application-specific errors."""
    
    def __init__(
        self, 
        status_code: int, 
        detail: str, 
        internal_code: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize AppException.
        
        Args:
            status_code: HTTP status code to return to client
            detail: Human-readable error message
            internal_code: Machine-readable error code for client applications
            data: Additional context data about the error
        """
        self.status_code = status_code
        self.detail = detail
        self.internal_code = internal_code
        self.data = data or {}
        super().__init__(detail)


class ValidationError(AppException):
    """Input validation error."""
    
    def __init__(
        self, 
        detail: str, 
        data: Optional[Dict[str, Any]] = None
    ):
        """Initialize with 400 status code and VALIDATION_ERROR code."""
        super().__init__(400, detail, "VALIDATION_ERROR", data)


class ProcessingError(AppException):
    """Error during data processing."""
    
    def __init__(
        self, 
        detail: str, 
        data: Optional[Dict[str, Any]] = None
    ):
        """Initialize with 500 status code and PROCESSING_ERROR code."""
        super().__init__(500, detail, "PROCESSING_ERROR", data)


class NotFoundError(AppException):
    """Resource not found error."""
    
    def __init__(
        self, 
        detail: str, 
        data: Optional[Dict[str, Any]] = None
    ):
        """Initialize with 404 status code and NOT_FOUND code."""
        super().__init__(404, detail, "NOT_FOUND", data)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handler for application exceptions.
    
    Returns a structured JSON response with error details.
    """
    logger.error(
        f"AppException: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "internal_code": exc.internal_code,
            "path": request.url.path,
            "data": exc.data
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": exc.internal_code,
            "data": exc.data
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handler for HTTP exceptions.
    
    Returns a simple JSON response with the error message.
    """
    logger.error(
        f"HTTPException: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler for request validation exceptions.
    
    Returns a JSON response with validation error details.
    """
    error_details = exc.errors()
    logger.error(
        "Validation error",
        extra={
            "errors": error_details,
            "path": request.url.path
        }
    )
    
    # Extract just the most relevant error information
    simplified_errors = []
    for error in error_details:
        simplified_errors.append({
            "loc": " > ".join([str(loc) for loc in error.get("loc", [])]),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": simplified_errors
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unhandled exceptions.
    
    Returns a generic error response and logs the full exception details.
    """
    error_details = traceback.format_exc()
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "traceback": error_details,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


def handle_exceptions(func: Callable) -> Callable:
    """
    Decorator to handle exceptions in route handlers.
    
    Catches exceptions and wraps them in appropriate AppException types.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AppException:
            # Already an AppException, just re-raise it
            raise
        except HTTPException:
            # Already an HTTPException, just re-raise it
            raise
        except ValueError as e:
            # Convert ValueError to ValidationError
            error_details = traceback.format_exc()
            logger.error(f"ValueError in {func.__name__}: {str(e)}\n{error_details}")
            raise ValidationError(f"Invalid input: {str(e)}")
        except Exception as e:
            # Wrap any other exception in ProcessingError
            error_details = traceback.format_exc()
            logger.error(f"Error in {func.__name__}: {str(e)}\n{error_details}")
            raise ProcessingError(f"An error occurred: {str(e)}")
    
    return wrapper

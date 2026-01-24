"""
Custom Exceptions and Error Handling

Unified error response format for the entire application.
All exceptions return: { success: false, message: "...", code: 400/500 }
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Any, Dict
import logging
import traceback

logger = logging.getLogger(__name__)


# ========================================
# Error Response Schema
# ========================================

class ErrorResponse(BaseModel):
    """Unified error response format"""
    success: bool = False
    message: str
    code: int
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


# ========================================
# Custom Exception Classes
# ========================================

class StyleXException(Exception):
    """Base exception for StyleX application"""
    
    def __init__(
        self,
        message: str,
        code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


class ValidationError(StyleXException):
    """Input validation failed"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class AuthenticationError(StyleXException):
    """Authentication failed"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(StyleXException):
    """User lacks permission"""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(StyleXException):
    """Resource not found"""
    
    def __init__(self, resource: str = "Resource", identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        super().__init__(
            message=message,
            code=status.HTTP_404_NOT_FOUND
        )


class ConflictError(StyleXException):
    """Resource conflict (duplicate, etc.)"""
    
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(
            message=message,
            code=status.HTTP_409_CONFLICT
        )


class ExternalServiceError(StyleXException):
    """External API/service failure"""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} service error: {message}",
            code=status.HTTP_502_BAD_GATEWAY,
            details={"service": service}
        )


class RateLimitError(StyleXException):
    """Rate limit exceeded"""
    
    def __init__(self, retry_after: Optional[int] = None):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after} if retry_after else None
        )


class ImageProcessingError(StyleXException):
    """Image processing failed"""
    
    def __init__(self, message: str = "Failed to process image"):
        super().__init__(
            message=message,
            code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class AIServiceError(StyleXException):
    """AI/ML model error"""
    
    def __init__(self, message: str = "AI service temporarily unavailable"):
        super().__init__(
            message=message,
            code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


# ========================================
# Exception Handlers
# ========================================

async def stylex_exception_handler(request: Request, exc: StyleXException) -> JSONResponse:
    """Handler for StyleX custom exceptions"""
    logger.warning(
        f"StyleX exception: {exc.message}",
        extra={
            "code": exc.code,
            "path": str(request.url),
            "method": request.method,
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=exc.code,
        content=ErrorResponse(
            success=False,
            message=exc.message,
            code=exc.code,
            details=exc.details
        ).model_dump()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for FastAPI HTTPException"""
    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={
            "code": exc.status_code,
            "path": str(request.url),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            message=str(exc.detail),
            code=exc.status_code
        ).model_dump()
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for Pydantic validation errors"""
    from pydantic import ValidationError as PydanticValidationError
    
    if isinstance(exc, PydanticValidationError):
        errors = exc.errors()
        message = "Validation failed"
        details = {"errors": [
            {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
            for e in errors
        ]}
    else:
        message = str(exc)
        details = None
    
    logger.warning(f"Validation error: {message}", extra={"details": details})
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            success=False,
            message=message,
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        ).model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unhandled exceptions"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": str(request.url),
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    # Don't expose internal details in production
    from app.config import settings
    message = str(exc) if settings.DEBUG else "An unexpected error occurred"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            message=message,
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ).model_dump()
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app"""
    from pydantic import ValidationError as PydanticValidationError
    from fastapi.exceptions import RequestValidationError
    
    app.add_exception_handler(StyleXException, stylex_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

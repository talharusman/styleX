"""
Common Utilities

Shared utilities, exceptions, caching, and logging across all modules.
"""

from .exceptions import (
    StyleXException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    ExternalServiceError,
    RateLimitError,
    ImageProcessingError,
    AIServiceError,
    ErrorResponse,
    register_exception_handlers
)

from .cache import (
    InMemoryCache,
    get_cache,
    cached,
    CacheNamespaces
)

from .logging_config import (
    setup_logging,
    RequestLogger
)

__all__ = [
    # Exceptions
    "StyleXException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "ExternalServiceError",
    "RateLimitError",
    "ImageProcessingError",
    "AIServiceError",
    "ErrorResponse",
    "register_exception_handlers",
    # Cache
    "InMemoryCache",
    "get_cache",
    "cached",
    "CacheNamespaces",
    # Logging
    "setup_logging",
    "RequestLogger"
]

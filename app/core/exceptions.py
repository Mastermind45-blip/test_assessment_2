"""Custom exceptions for the Weather App Backend.

This module defines application-specific exceptions that can be
used across all layers (services, controllers, etc.) and handled
by the global error handlers in the FastAPI application.
"""

from typing import Any, Dict, Optional


class WeatherAppException(Exception):
    """Base exception for all weather app errors.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code to return
        error_code: Machine-readable error code for API clients
        details: Optional additional error details
    """

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(WeatherAppException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(WeatherAppException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str = "Resource", resource_id: Optional[Any] = None):
        message = f"{resource} not found"
        if resource_id is not None:
            message = f"{resource} with ID {resource_id} not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
        )


class ExternalAPIError(WeatherAppException):
    """Raised when external API calls fail."""

    def __init__(self, api_name: str, message: str = "External API call failed"):
        super().__init__(
            message=f"{api_name}: {message}",
            status_code=503,
            error_code="EXTERNAL_API_ERROR",
            details={"api_name": api_name},
        )


class DatabaseError(WeatherAppException):
    """Raised when database operations fail."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
        )


class UnauthorizedError(WeatherAppException):
    """Raised when authentication/authorization fails."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
        )


class ForbiddenError(WeatherAppException):
    """Raised when user doesn't have permission."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
        )


class ConflictError(WeatherAppException):
    """Raised when there's a resource conflict (e.g., duplicate)."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
        )

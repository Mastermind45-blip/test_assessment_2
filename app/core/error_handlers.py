"""Global error handlers for FastAPI application.

This module contains exception handlers that convert custom exceptions
and standard exceptions into consistent JSON error responses.

The error response format follows RFC 7807 (Problem Details for HTTP APIs)
with extensions for the weather app.
"""

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import WeatherAppException

logger = logging.getLogger(__name__)


async def weather_app_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle custom WeatherAppException and its subclasses.

    Returns a standardized error response with:
    - status_code: HTTP status code
    - error.code: Machine-readable error code
    - error.message: Human-readable error message
    - error.details: Optional additional details
    """
    # Cast to WeatherAppException if it is one
    if not isinstance(exc, WeatherAppException):
        raise exc

    weather_exc: WeatherAppException = exc

    logger.error(
        f"WeatherAppException: {weather_exc.error_code} - {weather_exc.message}",
        extra={"details": weather_exc.details, "path": request.url.path},
    )

    content: Dict[str, Any] = {
        "error": {
            "code": weather_exc.error_code,
            "message": weather_exc.message,
        }
    }

    # Add details if present
    if weather_exc.details:
        content["error"]["details"] = weather_exc.details

    # Add request path for debugging (optional)
    if request:
        content["error"]["path"] = str(request.url.path)

    return JSONResponse(
        status_code=weather_exc.status_code,
        content=content,
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle FastAPI HTTPException.

    Converts Starlette/FastAPI HTTPException to our standard format.
    """
    from fastapi import HTTPException as FastAPIHTTPException

    if isinstance(exc, FastAPIHTTPException):
        logger.warning(
            f"HTTPException: {exc.status_code} - {exc.detail}",
            extra={"path": request.url.path},
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "path": str(request.url.path),
                }
            },
        )

    # Re-raise if not HTTPException
    raise exc


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Returns detailed validation error information.
    """
    from pydantic import ValidationError as PydanticValidationError

    if isinstance(exc, PydanticValidationError):
        logger.warning(
            f"Validation error: {exc.errors()}",
            extra={"path": request.url.path},
        )

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                    "path": str(request.url.path),
                }
            },
        )

    # Re-raise if not Pydantic ValidationError
    raise exc


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions.

    Catches any exception not handled by other handlers.
    Returns 500 Internal Server Error with generic message.
    """
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={"path": request.url.path},
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
                "path": str(request.url.path),
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI application.

    This function should be called during app initialization in main.py.

    Args:
        app: The FastAPI application instance
    """
    # Custom application exceptions
    app.add_exception_handler(WeatherAppException, weather_app_exception_handler)

    # HTTP exceptions (FastAPI/Starlette)
    from fastapi import HTTPException as FastAPIHTTPException

    app.add_exception_handler(FastAPIHTTPException, http_exception_handler)

    # Pydantic validation errors
    from pydantic import ValidationError as PydanticValidationError

    app.add_exception_handler(PydanticValidationError, validation_exception_handler)

    # Catch-all for unhandled exceptions
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered successfully")

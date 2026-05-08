"""Export API router - HTTP endpoints for data export.

This module defines the FastAPI router for export-related endpoints:
- POST /export/ - Export weather data in specified format
- GET /export/formats - Get available export formats
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.export_controller import (
    export_weather_data_controller,
    get_export_formats_controller,
)
from app.dependencies import get_db
from app.schemas.export import ExportRequest

router = APIRouter(
    prefix="/api/v1/export",
    tags=["Data Export"],
    responses={
        400: {"description": "Bad Request - Invalid export format or parameters"},
        404: {"description": "Not Found - No data to export"},
        422: {"description": "Validation Error - Invalid request body"},
        500: {"description": "Internal Server Error"},
    },
)


@router.post(
    "/",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
    summary="Export weather data",
    description="""
    Export weather data in the specified format.

    Supported formats:
    - JSON: JavaScript Object Notation
    - CSV: Comma-Separated Values
    - XLSX: Microsoft Excel format

    The export includes all weather records with their related data:
    - Weather forecasts
    - YouTube videos
    - Map location data

    Returns a file download response with appropriate content type.
    """,
)
async def export_weather_data(
    export_request: ExportRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export weather data in specified format."""
    return await export_weather_data_controller(export_request, db)


@router.get(
    "/formats",
    summary="Get available export formats",
    description="""
    Get a list of supported export formats.

    Returns format codes, names, descriptions, and content types
    that can be used with the export endpoint.
    """,
)
async def get_export_formats() -> dict:
    """Get available export formats."""
    return await get_export_formats_controller()

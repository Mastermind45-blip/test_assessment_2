"""Weather API router - HTTP endpoints for weather records.

This module defines the FastAPI router for weather-related endpoints:
- POST /weather/ - Create new weather record
- GET /weather/ - List weather records with pagination/filtering
- GET /weather/{record_id} - Get specific weather record
- PUT /weather/{record_id}/notes - Update notes (only updatable field)
- DELETE /weather/{record_id} - Delete weather record and related data
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.weather_controller import (
    create_weather_record_controller,
    delete_weather_record_controller,
    get_weather_record_controller,
    list_weather_records_controller,
    update_weather_notes_controller,
)
from app.dependencies import get_db
from app.schemas.weather import (
    WeatherRecordCreate,
    WeatherRecordResponse,
    WeatherRecordUpdate,
)

router = APIRouter(
    prefix="/api/v1/weather",
    tags=["Weather Records"],
    responses={
        400: {"description": "Bad Request - Invalid input data"},
        404: {"description": "Not Found - Weather record not found"},
        422: {"description": "Validation Error - Invalid request body"},
        500: {"description": "Internal Server Error"},
    },
)


@router.post(
    "/",
    response_model=WeatherRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new weather record",
    description="""
    Create a new weather record with all related data.

    This endpoint:
    - Validates location coordinates and date range
    - Fetches weather forecast from external API
    - Searches for related YouTube videos
    - Retrieves map location data
    - Stores everything in the database

    Only the following fields are required:
    - location_name: Name of the location
    - latitude: Between -90 and 90
    - longitude: Between -180 and 180
    - start_date: Start date for weather data
    - end_date: End date (must be >= start_date)
    """,
)
async def create_weather_record(
    weather_data: WeatherRecordCreate,
    db: AsyncSession = Depends(get_db),
) -> WeatherRecordResponse:
    """Create a new weather record with all related data."""
    return await create_weather_record_controller(weather_data, db)


@router.get(
    "/",
    response_model=List[WeatherRecordResponse],
    summary="List weather records",
    description="""
    List weather records with pagination and optional filtering.

    Query parameters:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100, max: 1000)
    - location_name: Optional filter by location name (partial match)
    """,
)
async def list_weather_records(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    location_name: Optional[str] = Query(
        None, description="Filter by location name (partial match)"
    ),
) -> List[WeatherRecordResponse]:
    """List weather records with pagination and filtering."""
    return await list_weather_records_controller(
        db, skip=skip, limit=limit, location_name=location_name
    )


@router.get(
    "/{record_id}",
    response_model=WeatherRecordResponse,
    summary="Get weather record by ID",
    description="""
    Get a specific weather record by ID with all related data.

    Returns:
    - Weather record details (location, dates, notes)
    - Weather forecast data (daily forecasts)
    - YouTube videos related to the location
    - Map location data
    """,
)
async def get_weather_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
) -> WeatherRecordResponse:
    """Get a weather record by ID with all related data."""
    return await get_weather_record_controller(record_id, db)


@router.put(
    "/{record_id}/notes",
    response_model=WeatherRecordResponse,
    summary="Update weather record notes",
    description="""
    Update the notes field for a weather record.

    Per requirements: Only the notes field can be updated by users.
    All other fields are read-only after creation.

    If the record doesn't exist, returns 404.
    """,
)
async def update_weather_notes(
    record_id: int,
    update_data: WeatherRecordUpdate,
    db: AsyncSession = Depends(get_db),
) -> WeatherRecordResponse:
    """Update notes for a weather record."""
    return await update_weather_notes_controller(record_id, update_data, db)


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete weather record",
    description="""
    Delete a weather record and all related data.

    Per requirements: Related data (forecasts, videos, map data) is
    cascade-deleted via database constraints.

    Returns 204 No Content on success.
    Returns 404 if record doesn't exist.
    """,
)
async def delete_weather_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a weather record and all related data."""
    await delete_weather_record_controller(record_id, db)

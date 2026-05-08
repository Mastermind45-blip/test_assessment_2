"""Dependency injection configuration for FastAPI application.

This module sets up all dependencies for the application layers:
- Database sessions
- Repositories
- Services
- Controllers

Uses FastAPI's Depends() for automatic dependency injection.
"""

from typing import List

from fastapi import Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.export_controller import (
    export_weather_data_controller,
    get_export_formats_controller,
)
from app.controllers.weather_controller import (
    create_weather_record_controller,
    delete_weather_record_controller,
    get_weather_record_controller,
    list_weather_records_controller,
    update_weather_notes_controller,
)
from app.core.database import get_db as get_db_session
from app.repositories.weather_repository import WeatherRepository
from app.schemas.export import ExportRequest
from app.schemas.weather import (
    WeatherRecordCreate,
    WeatherRecordResponse,
    WeatherRecordUpdate,
)
from app.services.weather_service import WeatherService

# Database dependency - reuse from database.py
# Already implemented in core/database.py, just re-export here
get_db = get_db_session


# Repository dependencies
def get_weather_repository(db: AsyncSession = Depends(get_db)) -> WeatherRepository:
    """Provide WeatherRepository instance.

    Args:
        db: Database session from dependency

    Returns:
        WeatherRepository: Repository for weather data access
    """
    return WeatherRepository(db)


# Service dependencies - WeatherService manages its own APIClientManager
# as shown in weather_service.py __init__ method


def get_weather_service(db: AsyncSession = Depends(get_db)) -> WeatherService:
    """Provide WeatherService instance.

    Args:
        db: Database session from dependency

    Returns:
        WeatherService: Service for weather business logic
    """
    return WeatherService(db)


# Controller dependencies (if controllers were classes, but they're functions)
# Since controllers are function-based, we'll create wrapper functions that
# combine service and controller logic for cleaner dependency injection


async def create_weather_record_endpoint(
    weather_data: WeatherRecordCreate,
    db: AsyncSession = Depends(get_db),
) -> WeatherRecordResponse:
    """Endpoint dependency for creating weather records.

    This function bridges the router to the controller with proper DI.
    """
    return await create_weather_record_controller(weather_data, db)


async def list_weather_records_endpoint(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    location_name: str = None,
) -> List[WeatherRecordResponse]:
    """Endpoint dependency for listing weather records."""
    return await list_weather_records_controller(
        db, skip=skip, limit=limit, location_name=location_name
    )


async def get_weather_record_endpoint(
    record_id: int,
    db: AsyncSession = Depends(get_db),
) -> WeatherRecordResponse:
    """Endpoint dependency for getting a weather record."""
    return await get_weather_record_controller(record_id, db)


async def update_weather_notes_endpoint(
    record_id: int,
    update_data: WeatherRecordUpdate,
    db: AsyncSession = Depends(get_db),
) -> WeatherRecordResponse:
    """Endpoint dependency for updating weather notes."""
    return await update_weather_notes_controller(record_id, update_data, db)


async def delete_weather_record_endpoint(
    record_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Endpoint dependency for deleting a weather record."""
    return await delete_weather_record_controller(record_id, db)


# Export controller dependencies
async def export_weather_data_endpoint(
    export_request: ExportRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Endpoint dependency for exporting weather data."""
    return await export_weather_data_controller(export_request, db)


async def get_export_formats_endpoint() -> dict:
    """Endpoint dependency for getting export formats."""
    return await get_export_formats_controller()


# Optional: If you want to use class-based controllers with DI
# Optional: If you want to use class-based controllers with DI
# Commented out because current implementation uses function-based controllers
# Uncomment if you want to refactor to class-based controllers

# class WeatherControllerFactory:
#     """Factory for creating weather controller functions with dependencies."""
#
#     @staticmethod
#     def create_record(
#         weather_data: WeatherRecordCreate,
#         db: AsyncSession = Depends(get_db),
#     ):
#         return create_weather_record_controller(weather_data, db)
#
#     @staticmethod
#     def list_records(
#         db: AsyncSession = Depends(get_db),
#         skip: int = 0,
#         limit: int = 100,
#         location_name: str = None,
#     ):
#         return list_weather_records_controller(
#             db, skip=skip, limit=limit, location_name=location_name
#         )
#
#     @staticmethod
#     def get_record(
#         record_id: int,
#         db: AsyncSession = Depends(get_db),
#     ):
#         return get_weather_record_controller(record_id, db)
#
#     @staticmethod
#     def update_notes(
#         record_id: int,
#         update_data: WeatherRecordUpdate,
#         db: AsyncSession = Depends(get_db),
#     ):
#         return update_weather_notes_controller(record_id, update_data, db)
#
#     @staticmethod
#     def delete_record(
#         record_id: int,
#         db: AsyncSession = Depends(get_db),
#     ):
#         return delete_weather_record_controller(record_id, db)
#
#
# class ExportControllerFactory:
#     """Factory for creating export controller functions with dependencies."""
#
#     @staticmethod
#     async def export_data(
#         export_request: ExportRequest,
#         db: AsyncSession = Depends(get_db),
#     ):
#         return await export_weather_data_controller(export_request, db)
#
#     @staticmethod
#     async def get_formats():
#         return await get_export_formats_controller()

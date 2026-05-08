"""Weather controller - HTTP layer for weather endpoints.

This module contains the controller functions that handle:
- HTTP request/response handling
- Delegation to weather service for business logic
- Uses custom exceptions from app.core.exceptions

Note: Router decorators and endpoint registration will be done in Task 3.2.
These controller functions are pure business logic handlers for HTTP layer.
"""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError, WeatherAppException
from app.schemas.weather import (
    WeatherRecordCreate,
    WeatherRecordResponse,
    WeatherRecordUpdate,
)
from app.services.weather_service import WeatherService


async def create_weather_record_controller(
    weather_data: WeatherRecordCreate,
    db: AsyncSession,
) -> WeatherRecordResponse:
    """Create a new weather record with all related data.

    Controller logic:
    - Delegates to service layer for business logic
    - Handles HTTP-specific errors and status codes
    - Returns response model
    """
    try:
        async with WeatherService(db) as service:
            result = await service.create_weather_record(weather_data)
            return WeatherRecordResponse.model_validate(result)
    except ValueError as e:
        raise ValidationError(message=str(e))
    except WeatherAppException:
        raise
    except Exception as e:
        raise WeatherAppException(
            message=f"Failed to create weather record: {str(e)}",
            status_code=500,
            error_code="CREATE_RECORD_ERROR",
        )


async def list_weather_records_controller(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    location_name: Optional[str] = None,
) -> List[WeatherRecordResponse]:
    """List weather records with pagination and filtering.

    Controller logic:
    - Delegates to service layer for business logic
    - Handles HTTP-specific errors and status codes
    - Returns list of response models
    """
    try:
        async with WeatherService(db) as service:
            results = await service.list_weather_records(
                skip=skip, limit=limit, location_name=location_name
            )
            return [WeatherRecordResponse.model_validate(r) for r in results]
    except WeatherAppException:
        raise
    except Exception as e:
        raise WeatherAppException(
            message=f"Failed to list weather records: {str(e)}",
            status_code=500,
            error_code="LIST_RECORDS_ERROR",
        )


async def get_weather_record_controller(
    record_id: int,
    db: AsyncSession,
) -> WeatherRecordResponse:
    """Get a weather record by ID with all related data.

    Controller logic:
    - Delegates to service layer for business logic
    - Handles 404 not found
    - Returns response model
    """
    try:
        async with WeatherService(db) as service:
            result = await service.get_weather_record(record_id)
            if not result:
                raise NotFoundError(
                    resource="Weather record",
                    resource_id=record_id,
                )
            return WeatherRecordResponse.model_validate(result)
    except WeatherAppException:
        raise
    except Exception as e:
        raise WeatherAppException(
            message=f"Failed to get weather record: {str(e)}",
            status_code=500,
            error_code="GET_RECORD_ERROR",
        )


async def update_weather_notes_controller(
    record_id: int,
    update_data: WeatherRecordUpdate,
    db: AsyncSession,
) -> WeatherRecordResponse:
    """Update notes for a weather record.

    Controller logic:
    - Delegates to service layer for business logic
    - Handles 404 not found
    - Returns response model
    """
    try:
        async with WeatherService(db) as service:
            result = await service.update_weather_notes(record_id, update_data)
            if not result:
                raise NotFoundError(
                    resource="Weather record",
                    resource_id=record_id,
                )
            return WeatherRecordResponse.model_validate(result)
    except WeatherAppException:
        raise
    except Exception as e:
        raise WeatherAppException(
            message=f"Failed to update notes: {str(e)}",
            status_code=500,
            error_code="UPDATE_NOTES_ERROR",
        )


async def delete_weather_record_controller(
    record_id: int,
    db: AsyncSession,
) -> None:
    """Delete a weather record and all related data.

    Controller logic:
    - Delegates to service layer for business logic
    - Handles 404 not found
    - Returns 204 No Content on success
    """
    try:
        async with WeatherService(db) as service:
            deleted = await service.delete_weather_record(record_id)
            if not deleted:
                raise NotFoundError(
                    resource="Weather record",
                    resource_id=record_id,
                )
    except WeatherAppException:
        raise
    except Exception as e:
        raise WeatherAppException(
            message=f"Failed to delete weather record: {str(e)}",
            status_code=500,
            error_code="DELETE_RECORD_ERROR",
        )

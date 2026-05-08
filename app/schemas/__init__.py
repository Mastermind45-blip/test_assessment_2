"""Pydantic schemas for Weather App Backend."""

from app.schemas.export import ExportRequest, ExportResponse
from app.schemas.weather import (
    MapLocationData,
    WeatherForecastData,
    WeatherRecordCreate,
    WeatherRecordResponse,
    WeatherRecordUpdate,
    YouTubeVideoData,
)

__all__ = [
    # Weather Record schemas (main use case)
    "WeatherRecordCreate",
    "WeatherRecordResponse",
    "WeatherRecordUpdate",
    "WeatherForecastData",
    "YouTubeVideoData",
    "MapLocationData",
    # Export schemas
    "ExportRequest",
    "ExportResponse",
]

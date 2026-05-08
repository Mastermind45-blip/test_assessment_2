"""Weather record schemas for API requests and responses.

This module contains Pydantic schemas for the main use case:
- Weather record creation with coordinates and date range
- Weather record updates (notes only per requirements)
- Weather record responses with all related data (forecasts, videos, map data)
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class WeatherRecordCreate(BaseModel):
    """Schema for creating a new weather record with all related data.

    This is the main input schema for the application's core feature:
    - Accepts coordinates directly (latitude/longitude)
    - Triggers external API calls (weather, YouTube, maps)
    - Creates weather record with all related data
    """

    location_name: str
    latitude: float
    longitude: float
    start_date: date
    end_date: date
    user_notes: Optional[str] = None

    @field_validator("latitude")
    def validate_latitude(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        return v

    @field_validator("longitude")
    def validate_longitude(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        return v

    @field_validator("end_date")
    def validate_date_range(cls, v: date, info) -> date:
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("End date must be after or equal to start date")
        return v


class WeatherRecordUpdate(BaseModel):
    """Schema for updating weather record.

    Per requirements: Only notes can be updated by users.
    Other fields are read-only after creation.
    """

    user_notes: Optional[str] = None


class WeatherForecastData(BaseModel):
    """Schema for weather forecast data in response."""

    id: int
    forecast_date: date
    temperature: Optional[float] = None
    feels_like: Optional[float] = None
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    humidity: Optional[int] = None
    pressure: Optional[int] = None
    wind_speed: Optional[float] = None
    weather_description: Optional[str] = None
    icon_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class YouTubeVideoData(BaseModel):
    """Schema for YouTube video data in response."""

    id: int
    video_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    channel_title: Optional[str] = None
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MapLocationData(BaseModel):
    """Schema for map location data in response."""

    id: int
    place_id: Optional[str] = None
    formatted_address: Optional[str] = None
    map_url: Optional[str] = None
    static_map_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    place_type: Optional[str] = None
    point_of_interest: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class WeatherRecordResponse(BaseModel):
    """Schema for weather record response with all related data.

    This is the main response schema that includes:
    - Weather record details (location, dates, notes)
    - Weather forecast data (daily forecasts)
    - YouTube videos related to location
    - Map location data
    """

    id: int
    location_name: str
    latitude: float
    longitude: float
    start_date: date
    end_date: date
    user_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Related data
    weather_forecasts: List[WeatherForecastData] = []
    youtube_videos: List[YouTubeVideoData] = []
    map_location: Optional[MapLocationData] = None

    model_config = ConfigDict(from_attributes=True)

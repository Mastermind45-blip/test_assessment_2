from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class Coordinate(BaseModel):
    """Schema for validating geographic coordinates."""

    latitude: float
    longitude: float

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


class LocationNested(BaseModel):
    """Nested schema for Location data embedded in Weather responses."""

    id: int
    name: str
    latitude: float
    longitude: float
    country_code: str

    model_config = ConfigDict(from_attributes=True)


class WeatherBase(BaseModel):
    """Base schema with common Weather fields."""

    temperature: float
    humidity: int
    weather_condition: str
    notes: Optional[str] = None
    weather_date: date

    @field_validator("humidity")
    def validate_humidity(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("Humidity must be between 0 and 100 percent")
        return v

    @field_validator("weather_date")
    def validate_weather_date(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Weather date cannot be in the future")
        return v


class WeatherCreate(WeatherBase):
    """Schema for creating new Weather records."""

    location_id: int


class WeatherUpdate(BaseModel):
    """Schema for updating Weather records (only notes can be updated per service plan)."""

    notes: Optional[str] = None


class WeatherResponse(WeatherBase):
    """Schema for Weather response data, including nested Location."""

    id: int
    location: LocationNested
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

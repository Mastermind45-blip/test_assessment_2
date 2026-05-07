"""Weather service - Core business logic for weather records.

This module contains the main service class that orchestrates:
- Input validation
- External API calls (weather, YouTube, maps)
- Database operations via repository
- Error handling and business rules
"""

import logging
from datetime import date
from typing import List, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.api_clients import APIClientManager
from app.models.weather import WeatherRecord
from app.repositories.weather_repository import WeatherRepository
from app.schemas.weather import WeatherRecordCreate, WeatherRecordUpdate

logger = logging.getLogger(__name__)


class WeatherService:
    """Service class for weather record business logic.

    This service orchestrates:
    1. Validation of input data
    2. Calls to external APIs (weather, YouTube, maps)
    3. Database operations via repository pattern
    4. Error handling and business rules
    """

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.repository = WeatherRepository(db)
        self.api_manager = APIClientManager()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close API clients."""
        await self.api_manager.close_all()

    async def create_weather_record(
        self, weather_data: WeatherRecordCreate
    ) -> WeatherRecord:
        """Create a new weather record with all related data.

        Business logic:
        1. Validate date range (already done by Pydantic)
        2. Fetch weather forecast from external API
        3. Fetch YouTube videos related to location
        4. Fetch map data for location
        5. Save everything to database

        Args:
            weather_data: Validated weather record creation schema

        Returns:
            Created weather record with all related data

        Raises:
            ValueError: If validation fails
            Exception: If external API calls fail
        """
        try:
            # Convert schema to dict for repository
            record_dict = weather_data.model_dump()

            # Create main weather record
            weather_record = await self.repository.create_weather_record(record_dict)

            if not weather_record:
                raise ValueError("Failed to create weather record")

            # Query the record we just created to get the ID
            # Use location_name to find the most recent record
            records = await self.repository.get_all_weather_records(
                location_name=weather_data.location_name, limit=1
            )

            if not records:
                raise ValueError("Failed to retrieve created record")

            # Access id directly - SQLAlchemy should populate this after flush/refresh
            # Use getattr for safety
            record_id_col = getattr(records[0], "id", None)
            if record_id_col is None:
                raise ValueError("Record has no ID attribute")

            # Convert to int - this should work if it's actually an int value
            try:
                record_id = int(record_id_col)
            except (TypeError, ValueError):
                # If direct conversion fails, try to get the value differently
                # This handles cases where SQLAlchemy returns Column objects
                record_id = records[0].__dict__.get("id")
                if record_id is None:
                    raise ValueError("Could not extract record ID")
                record_id = int(record_id)

            # Fetch and store weather forecast data
            await self._fetch_and_store_weather_data(
                record_id,
                weather_data.latitude,
                weather_data.longitude,
                weather_data.start_date,
                weather_data.end_date,
            )

            # Fetch and store YouTube videos
            await self._fetch_and_store_youtube_videos(
                record_id, weather_data.location_name
            )

            # Fetch and store map location data
            await self._fetch_and_store_map_location(
                record_id,
                weather_data.latitude,
                weather_data.longitude,
            )

            # Return complete record with all relations
            result = await self.repository.get_weather_record_by_id(record_id)
            if not result:
                raise ValueError("Failed to retrieve created weather record")
            return result

        except Exception as e:
            logger.error(f"Error creating weather record: {str(e)}")
            raise

    async def get_weather_record(self, record_id: int) -> Optional[WeatherRecord]:
        """Get a weather record by ID with all related data.

        Args:
            record_id: ID of the weather record

        Returns:
            Weather record if found, None otherwise
        """
        return await self.repository.get_weather_record_by_id(record_id)

    async def list_weather_records(
        self,
        skip: int = 0,
        limit: int = 100,
        location_name: Optional[str] = None,
    ) -> List[WeatherRecord]:
        """List weather records with pagination and filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            location_name: Optional filter by location name

        Returns:
            List of weather records
        """
        return await self.repository.get_all_weather_records(
            skip=skip, limit=limit, location_name=location_name
        )

    async def update_weather_notes(
        self, record_id: int, update_data: WeatherRecordUpdate
    ) -> Optional[WeatherRecord]:
        """Update notes for a weather record.

        Per requirements: Only notes can be updated by users.

        Args:
            record_id: ID of the weather record
            update_data: Validated update schema

        Returns:
            Updated weather record if found, None otherwise
        """
        if update_data.user_notes is None:
            # No update needed
            return await self.repository.get_weather_record_by_id(record_id)

        return await self.repository.update_notes(record_id, update_data.user_notes)

    async def delete_weather_record(self, record_id: int) -> bool:
        """Delete a weather record and all related data.

        Per requirements: Related data is cascade-deleted.

        Args:
            record_id: ID of the weather record to delete

        Returns:
            True if deleted, False if not found
        """
        return await self.repository.delete_weather_record(record_id)

    async def _fetch_and_store_weather_data(
        self,
        record_id: int,
        lat: float,
        lon: float,
        start_date: date,
        end_date: date,
    ) -> None:
        """Fetch weather forecast and store in database.

        Args:
            record_id: Weather record ID
            lat: Latitude
            lon: Longitude
            start_date: Start date for forecast
            end_date: End date for forecast
        """
        try:
            # Calculate number of days
            days = (end_date - start_date).days + 1
            days = min(days, 7)  # Limit to 7 days for free tier

            # Fetch forecast from API
            forecast_data = await self.api_manager.weather_client.get_forecast(
                lat, lon, days
            )

            # Prepare data for bulk insert
            weather_data_list = []
            for day_data in forecast_data:
                weather_data_list.append(
                    {
                        "weather_record_id": record_id,
                        "forecast_date": day_data["forecast_date"],
                        "temperature": day_data.get("temperature"),
                        "feels_like": day_data.get("feels_like"),
                        "temp_min": day_data.get("temp_min"),
                        "temp_max": day_data.get("temp_max"),
                        "humidity": day_data.get("humidity"),
                        "pressure": day_data.get("pressure"),
                        "wind_speed": day_data.get("wind_speed"),
                        "weather_description": day_data.get("weather_description"),
                        "icon_code": day_data.get("icon_code"),
                    }
                )

            # Bulk create weather data
            if weather_data_list:
                await self.repository.create_weather_data(weather_data_list)

        except Exception as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            # Don't raise - we still want to save the main record
            # In production, you might want to handle this differently

    async def _fetch_and_store_youtube_videos(
        self, record_id: int, location_name: str
    ) -> None:
        """Fetch YouTube videos and store in database.

        Args:
            record_id: Weather record ID
            location_name: Location name for search query
        """
        try:
            # Search for videos
            query = f"weather {location_name}"
            videos = await self.api_manager.youtube_client.search_videos(
                query, max_results=5
            )

            # Prepare data for bulk insert
            video_list = []
            for video in videos:
                video_list.append(
                    {
                        "weather_record_id": record_id,
                        "video_id": video["video_id"],
                        "title": video.get("title"),
                        "description": video.get("description"),
                        "url": video.get("url"),
                        "thumbnail_url": video.get("thumbnail_url"),
                        "channel_title": video.get("channel_title"),
                        "published_at": video.get("published_at"),
                    }
                )

            # Bulk create videos
            if video_list:
                await self.repository.create_youtube_videos(video_list)

        except Exception as e:
            logger.error(f"Error fetching YouTube videos: {str(e)}")
            # Don't raise - non-critical feature

    async def _fetch_and_store_map_location(
        self, record_id: int, lat: float, lon: float
    ) -> None:
        """Fetch map location data and store in database.

        Args:
            record_id: Weather record ID
            lat: Latitude
            lon: Longitude
        """
        try:
            # Get place details
            place_data = await self.api_manager.maps_client.get_place_details(lat, lon)

            if place_data:
                # Prepare data for insert
                location_data = {
                    "weather_record_id": record_id,
                    "place_id": place_data.get("place_id"),
                    "formatted_address": place_data.get("formatted_address"),
                    "map_url": place_data.get("map_url"),
                    "static_map_url": place_data.get("static_map_url"),
                    "lat": place_data.get("lat"),
                    "lng": place_data.get("lng"),
                    "place_type": place_data.get("place_type"),
                    "point_of_interest": place_data.get("point_of_interest"),
                }

                # Create map location
                await self.repository.create_map_location(location_data)

        except Exception as e:
            logger.error(f"Error fetching map data: {str(e)}")
            # Don't raise - non-critical feature

    async def fetch_additional_api_data(
        self, record_id: int, api_name: str, endpoint: str, params: dict
    ) -> None:
        """Fetch additional API data and store in database.

        This is a generic method for fetching data from additional APIs.

        Args:
            record_id: Weather record ID
            api_name: Name of the API (for reference)
            endpoint: API endpoint URL
            params: Query parameters
        """
        try:
            # Make API call
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                payload = response.json()

            # Store in database
            api_data_list = [
                {
                    "weather_record_id": record_id,
                    "api_name": api_name,
                    "data_type": "json",
                    "payload": payload,
                }
            ]

            await self.repository.create_additional_api_data(api_data_list)

        except Exception as e:
            logger.error(f"Error fetching additional API data: {str(e)}")
            raise

"""Repository for WeatherRecord and related models database operations."""

from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weather import (
    AdditionalApiData,
    MapLocation,
    WeatherData,
    WeatherRecord,
    YoutubeVideo,
)


class WeatherRepository:
    """Repository for WeatherRecord database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # WeatherRecord operations
    async def create_weather_record(self, weather_data: dict) -> WeatherRecord:
        """Create a new weather record."""
        try:
            weather_record = WeatherRecord(**weather_data)
            self.db.add(weather_record)
            await self.db.flush()
            await self.db.refresh(weather_record)
            return weather_record
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def get_weather_record_by_id(self, record_id: int) -> Optional[WeatherRecord]:
        """Get weather record by ID."""
        query = select(WeatherRecord).where(WeatherRecord.id == record_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_weather_records(
        self, skip: int = 0, limit: int = 100, location_name: Optional[str] = None
    ) -> List[WeatherRecord]:
        """Get all weather records with pagination and optional location filter."""
        query = select(WeatherRecord)

        if location_name:
            query = query.where(WeatherRecord.location_name.ilike(f"%{location_name}%"))

        query = (
            query.offset(skip).limit(limit).order_by(WeatherRecord.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_notes(
        self, record_id: int, user_notes: str
    ) -> Optional[WeatherRecord]:
        """Update notes for a weather record (UPDATE operation from requirements)."""
        query = (
            update(WeatherRecord)
            .where(WeatherRecord.id == record_id)
            .values(user_notes=user_notes, updated_at=WeatherRecord.updated_at)
            .returning(WeatherRecord)
        )
        result = await self.db.execute(query)
        await self.db.flush()
        return result.scalar_one_or_none()

    async def delete_weather_record(self, record_id: int) -> bool:
        """Delete a weather record (DELETE operation from requirements).

        Note: Cascade delete will handle related records automatically.
        """
        weather_record = await self.get_weather_record_by_id(record_id)
        if weather_record:
            await self.db.delete(weather_record)
            await self.db.flush()
            return True
        return False

    # WeatherData operations
    async def create_weather_data(
        self, weather_data_list: List[dict]
    ) -> List[WeatherData]:
        """Create multiple weather data records."""
        try:
            weather_data_objects = [WeatherData(**data) for data in weather_data_list]
            self.db.add_all(weather_data_objects)
            await self.db.flush()
            for obj in weather_data_objects:
                await self.db.refresh(obj)
            return weather_data_objects
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    # YoutubeVideo operations
    async def create_youtube_videos(self, video_list: List[dict]) -> List[YoutubeVideo]:
        """Create multiple YouTube video records."""
        try:
            video_objects = [YoutubeVideo(**video) for video in video_list]
            self.db.add_all(video_objects)
            await self.db.flush()
            for obj in video_objects:
                await self.db.refresh(obj)
            return video_objects
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    # MapLocation operations
    async def create_map_location(self, location_data: dict) -> MapLocation:
        """Create a map location record."""
        try:
            location = MapLocation(**location_data)
            self.db.add(location)
            await self.db.flush()
            await self.db.refresh(location)
            return location
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    # AdditionalApiData operations
    async def create_additional_api_data(
        self, api_data_list: List[dict]
    ) -> List[AdditionalApiData]:
        """Create multiple additional API data records."""
        try:
            api_objects = [AdditionalApiData(**data) for data in api_data_list]
            self.db.add_all(api_objects)
            await self.db.flush()
            for obj in api_objects:
                await self.db.refresh(obj)
            return api_objects
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

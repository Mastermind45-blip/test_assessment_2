from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weather import WeatherRecord


class WeatherRepository:
    """Repository for WeatherRecord database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, weather_data: dict) -> WeatherRecord:
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

    async def get_by_id(self, record_id: int) -> Optional[WeatherRecord]:
        """Get weather record by ID (excluding deleted)."""
        query = select(WeatherRecord).where(
            WeatherRecord.id == record_id, WeatherRecord.is_deleted == False
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, city: Optional[str] = None
    ) -> List[WeatherRecord]:
        """Get all weather records with pagination and optional city filter."""
        query = select(WeatherRecord).where(WeatherRecord.is_deleted == False)

        if city:
            query = query.where(WeatherRecord.city.ilike(f"%{city}%"))

        query = (
            query.offset(skip).limit(limit).order_by(WeatherRecord.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_notes(self, record_id: int, notes: str) -> Optional[WeatherRecord]:
        """Update notes for a weather record (UPDATE operation from requirements)."""
        query = (
            update(WeatherRecord)
            .where(WeatherRecord.id == record_id, WeatherRecord.is_deleted == False)
            .values(notes=notes, updated_at=WeatherRecord.updated_at)
            .returning(WeatherRecord)
        )
        result = await self.db.execute(query)
        await self.db.flush()
        return result.scalar_one_or_none()

    async def delete(self, record_id: int) -> bool:
        """Soft delete a weather record (DELETE operation from requirements)."""
        query = (
            update(WeatherRecord)
            .where(WeatherRecord.id == record_id, WeatherRecord.is_deleted == False)
            .values(is_deleted=True, updated_at=WeatherRecord.updated_at)
        )
        result = await self.db.execute(query)
        await self.db.flush()
        return result.rowcount > 0

    async def get_by_city_and_country(
        self, city: str, country: Optional[str] = None
    ) -> List[WeatherRecord]:
        """Get weather records by city and optionally country."""
        query = select(WeatherRecord).where(
            WeatherRecord.city.ilike(city), WeatherRecord.is_deleted == False
        )

        if country:
            query = query.where(WeatherRecord.country == country.upper())

        query = query.order_by(WeatherRecord.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

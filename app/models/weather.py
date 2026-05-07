from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class WeatherRecord(Base):
    """Main weather record table - stores user requests."""

    __tablename__ = "weather_record"

    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String(255), nullable=False, unique=True, index=True)
    location_type = Column(
        String(50),
        nullable=False,
        # Check constraint will be added in migration
    )
    latitude = Column(Float(precision=10, decimal_return_scale=8), nullable=False)
    longitude = Column(Float(precision=11, decimal_return_scale=8), nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    user_notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    weather_data = relationship(
        "WeatherData", back_populates="weather_record", cascade="all, delete-orphan"
    )
    youtube_videos = relationship(
        "YoutubeVideo", back_populates="weather_record", cascade="all, delete-orphan"
    )
    map_locations = relationship(
        "MapLocation", back_populates="weather_record", cascade="all, delete-orphan"
    )
    additional_api_data = relationship(
        "AdditionalApiData",
        back_populates="weather_record",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="valid_date_range"),
        CheckConstraint(
            "location_type IN ('city', 'zip_code', 'coordinates', 'landmark')",
            name="valid_location_type",
        ),
    )

    def __repr__(self):
        return f"<WeatherRecord(id={self.id}, location='{self.location_name}', dates={self.start_date} to {self.end_date})>"


class WeatherData(Base):
    """Daily weather forecast data."""

    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    weather_record_id = Column(
        Integer,
        ForeignKey("weather_record.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    forecast_date = Column(Date, nullable=False)
    temperature = Column(Float(precision=5, decimal_return_scale=2), nullable=True)
    feels_like = Column(Float(precision=5, decimal_return_scale=2), nullable=True)
    temp_min = Column(Float(precision=5, decimal_return_scale=2), nullable=True)
    temp_max = Column(Float(precision=5, decimal_return_scale=2), nullable=True)
    humidity = Column(Integer, nullable=True)
    pressure = Column(Integer, nullable=True)
    wind_speed = Column(Float(precision=5, decimal_return_scale=2), nullable=True)
    weather_description = Column(String(100), nullable=True)
    icon_code = Column(String(20), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    weather_record = relationship("WeatherRecord", back_populates="weather_data")

    # Unique constraint for record + date combination
    __table_args__ = (
        UniqueConstraint(
            "weather_record_id", "forecast_date", name="uq_record_forecast_date"
        ),
    )

    def __repr__(self):
        return f"<WeatherData(id={self.id}, record_id={self.weather_record_id}, date={self.forecast_date})>"


class YoutubeVideo(Base):
    """YouTube videos related to weather location."""

    __tablename__ = "youtube_video"

    id = Column(Integer, primary_key=True, index=True)
    weather_record_id = Column(
        Integer,
        ForeignKey("weather_record.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    video_id = Column(String(20), nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String(255), nullable=True)
    thumbnail_url = Column(String(255), nullable=True)
    channel_title = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    weather_record = relationship("WeatherRecord", back_populates="youtube_videos")

    def __repr__(self):
        return f"<YoutubeVideo(id={self.id}, record_id={self.weather_record_id}, title='{self.title}')>"


class MapLocation(Base):
    """Google Maps location data."""

    __tablename__ = "map_location"

    id = Column(Integer, primary_key=True, index=True)
    weather_record_id = Column(
        Integer,
        ForeignKey("weather_record.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    place_id = Column(String(255), nullable=True)
    formatted_address = Column(Text, nullable=True)
    map_url = Column(String(500), nullable=True)
    static_map_url = Column(String(500), nullable=True)
    lat = Column(Float(precision=10, decimal_return_scale=8), nullable=True)
    lng = Column(Float(precision=11, decimal_return_scale=8), nullable=True)
    place_type = Column(String(50), nullable=True)
    point_of_interest = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    weather_record = relationship("WeatherRecord", back_populates="map_locations")

    def __repr__(self):
        return f"<MapLocation(id={self.id}, record_id={self.weather_record_id}, place='{self.point_of_interest}')>"


class AdditionalApiData(Base):
    """Flexible storage for additional API data (JSON payload)."""

    __tablename__ = "additional_api_data"

    id = Column(Integer, primary_key=True, index=True)
    weather_record_id = Column(
        Integer,
        ForeignKey("weather_record.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    api_name = Column(String(100), nullable=False)
    data_type = Column(String(50), nullable=True)
    payload = Column(JSON, nullable=True)  # Using JSON for flexibility
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    weather_record = relationship("WeatherRecord", back_populates="additional_api_data")

    def __repr__(self):
        return f"<AdditionalApiData(id={self.id}, record_id={self.weather_record_id}, api='{self.api_name}')>"

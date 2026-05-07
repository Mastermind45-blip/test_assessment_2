"""Multi-format export logic for weather data.

This module provides exporters to convert weather records
into various formats (JSON, CSV, Excel) for download.
"""

import csv
import io
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import openpyxl
from openpyxl.styles import Font, PatternFill
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weather import WeatherRecord
from app.repositories.weather_repository import WeatherRepository

logger = logging.getLogger(__name__)


class WeatherExporter:
    """Base exporter class with common utilities."""

    def __init__(self, db: AsyncSession):
        """Initialize exporter with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.repository = WeatherRepository(db)

    async def get_record_with_relations(
        self, record_id: int
    ) -> Optional[WeatherRecord]:
        """Fetch weather record with all related data.

        Args:
            record_id: ID of the weather record

        Returns:
            Weather record with relations if found, None otherwise
        """
        return await self.repository.get_weather_record_by_id(record_id)


class JSONExporter(WeatherExporter):
    """Export weather data to JSON format."""

    async def export(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Export weather record to JSON-serializable dictionary.

        Args:
            record_id: ID of the weather record

        Returns:
            Dictionary representation of the record, or None if not found
        """
        record = await self.get_record_with_relations(record_id)
        if not record:
            logger.warning(f"Record {record_id} not found for JSON export")
            return None

        try:
            return self._serialize_record(record)
        except Exception as e:
            logger.error(f"Error exporting record {record_id} to JSON: {str(e)}")
            raise

    def _serialize_record(self, record: WeatherRecord) -> Dict[str, Any]:
        """Serialize a weather record to dictionary.

        Args:
            record: WeatherRecord instance

        Returns:
            Dictionary representation
        """
        # Base record data
        result = {
            "id": record.id,
            "location_name": record.location_name,
            "location_type": record.location_type,
            "latitude": float(record.latitude) if record.latitude else None,
            "longitude": float(record.longitude) if record.longitude else None,
            "start_date": record.start_date.isoformat() if record.start_date else None,
            "end_date": record.end_date.isoformat() if record.end_date else None,
            "user_notes": record.user_notes,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }

        # Weather data (daily forecasts)
        if record.weather_data:
            result["weather_data"] = [
                {
                    "forecast_date": wd.forecast_date.isoformat()
                    if wd.forecast_date
                    else None,
                    "temperature": wd.temperature,
                    "feels_like": wd.feels_like,
                    "temp_min": wd.temp_min,
                    "temp_max": wd.temp_max,
                    "humidity": wd.humidity,
                    "pressure": wd.pressure,
                    "wind_speed": wd.wind_speed,
                    "weather_description": wd.weather_description,
                    "icon_code": wd.icon_code,
                }
                for wd in record.weather_data
            ]

        # YouTube videos
        if record.youtube_videos:
            result["youtube_videos"] = [
                {
                    "video_id": yv.video_id,
                    "title": yv.title,
                    "description": yv.description,
                    "url": yv.url,
                    "thumbnail_url": yv.thumbnail_url,
                    "channel_title": yv.channel_title,
                    "published_at": yv.published_at,
                }
                for yv in record.youtube_videos
            ]

        # Map locations
        if record.map_locations:
            result["map_locations"] = [
                {
                    "place_id": ml.place_id,
                    "formatted_address": ml.formatted_address,
                    "map_url": ml.map_url,
                    "static_map_url": ml.static_map_url,
                    "latitude": float(ml.lat) if ml.lat else None,
                    "longitude": float(ml.lng) if ml.lng else None,
                    "place_type": ml.place_type,
                    "point_of_interest": ml.point_of_interest,
                }
                for ml in record.map_locations
            ]

        # Additional API data
        if record.additional_api_data:
            result["additional_api_data"] = [
                {
                    "api_name": ad.api_name,
                    "data_type": ad.data_type,
                    "payload": ad.payload,
                    "fetched_at": ad.fetched_at.isoformat() if ad.fetched_at else None,
                }
                for ad in record.additional_api_data
            ]

        return result


class CSVExporter(WeatherExporter):
    """Export weather data to CSV format."""

    async def export(self, record_id: int) -> Optional[str]:
        """Export weather record to CSV string.

        Args:
            record_id: ID of the weather record

        Returns:
            CSV string, or None if record not found
        """
        record = await self.get_record_with_relations(record_id)
        if not record:
            logger.warning(f"Record {record_id} not found for CSV export")
            return None

        try:
            output = io.StringIO()
            writer = csv.writer(output)

            # Write main record info
            writer.writerow(["Weather Record Export"])
            writer.writerow([])
            writer.writerow(["Record ID", record.id])
            writer.writerow(["Location Name", record.location_name])
            writer.writerow(["Location Type", record.location_type])
            writer.writerow(["Latitude", record.latitude])
            writer.writerow(["Longitude", record.longitude])
            writer.writerow(["Start Date", record.start_date])
            writer.writerow(["End Date", record.end_date])
            writer.writerow(["User Notes", record.user_notes or ""])
            writer.writerow([])

            # Write weather data
            if record.weather_data:
                writer.writerow(["Weather Forecast Data"])
                writer.writerow(
                    [
                        "Date",
                        "Temperature (°C)",
                        "Feels Like (°C)",
                        "Min Temp (°C)",
                        "Max Temp (°C)",
                        "Humidity (%)",
                        "Pressure (hPa)",
                        "Wind Speed (m/s)",
                        "Description",
                    ]
                )
                for wd in sorted(
                    record.weather_data, key=lambda x: x.forecast_date or ""
                ):
                    writer.writerow(
                        [
                            wd.forecast_date,
                            wd.temperature,
                            wd.feels_like,
                            wd.temp_min,
                            wd.temp_max,
                            wd.humidity,
                            wd.pressure,
                            wd.wind_speed,
                            wd.weather_description or "",
                        ]
                    )
                writer.writerow([])

            # Write YouTube videos
            if record.youtube_videos:
                writer.writerow(["YouTube Videos"])
                writer.writerow(["Title", "Channel", "URL", "Published At"])
                for yv in record.youtube_videos:
                    writer.writerow(
                        [
                            yv.title or "",
                            yv.channel_title or "",
                            yv.url or "",
                            yv.published_at or "",
                        ]
                    )
                writer.writerow([])

            # Write map locations
            if record.map_locations:
                writer.writerow(["Map Locations"])
                writer.writerow(
                    ["Address", "Map URL", "Place Type", "Point of Interest"]
                )
                for ml in record.map_locations:
                    writer.writerow(
                        [
                            ml.formatted_address or "",
                            ml.map_url or "",
                            ml.place_type or "",
                            ml.point_of_interest or "",
                        ]
                    )

            return output.getvalue()

        except Exception as e:
            logger.error(f"Error exporting record {record_id} to CSV: {str(e)}")
            raise


class ExcelExporter(WeatherExporter):
    """Export weather data to Excel format."""

    async def export(self, record_id: int) -> Optional[bytes]:
        """Export weather record to Excel file bytes.

        Args:
            record_id: ID of the weather record

        Returns:
            Excel file as bytes, or None if record not found
        """
        record = await self.get_record_with_relations(record_id)
        if not record:
            logger.warning(f"Record {record_id} not found for Excel export")
            return None

        try:
            workbook = openpyxl.Workbook()
            # Remove default sheet
            workbook.remove(workbook.active)

            # Create sheets
            self._create_summary_sheet(workbook, record)
            if record.weather_data:
                self._create_weather_data_sheet(workbook, record)
            if record.youtube_videos:
                self._create_youtube_sheet(workbook, record)
            if record.map_locations:
                self._create_map_sheet(workbook, record)

            # Save to bytes
            excel_buffer = io.BytesIO()
            workbook.save(excel_buffer)
            excel_buffer.seek(0)

            return excel_buffer.read()

        except Exception as e:
            logger.error(f"Error exporting record {record_id} to Excel: {str(e)}")
            raise

    def _create_summary_sheet(self, workbook: openpyxl.Workbook, record: WeatherRecord):
        """Create summary sheet with record details.

        Args:
            workbook: openpyxl Workbook instance
            record: WeatherRecord instance
        """
        sheet = workbook.create_sheet("Summary")

        # Header style
        header_font = Font(bold=True, size=14)
        label_font = Font(bold=True)

        # Title
        sheet["A1"] = "Weather Record Export"
        sheet["A1"].font = header_font
        sheet["A1"].fill = PatternFill(
            start_color="E0E0E0", end_color="E0E0E0", fill_type="solid"
        )

        # Record details
        details = [
            ("Record ID", record.id),
            ("Location Name", record.location_name),
            ("Location Type", record.location_type),
            ("Latitude", record.latitude),
            ("Longitude", record.longitude),
            ("Start Date", record.start_date),
            ("End Date", record.end_date),
            ("User Notes", record.user_notes or ""),
            ("Created At", record.created_at),
            ("Updated At", record.updated_at),
        ]

        for idx, (label, value) in enumerate(details, start=3):
            cell_label = sheet[f"A{idx}"]
            cell_label.value = label
            cell_label.font = label_font

            cell_value = sheet[f"B{idx}"]
            cell_value.value = value

    def _create_weather_data_sheet(
        self, workbook: openpyxl.Workbook, record: WeatherRecord
    ):
        """Create weather data sheet.

        Args:
            workbook: openpyxl Workbook instance
            record: WeatherRecord instance
        """
        sheet = workbook.create_sheet("Weather Data")

        # Headers
        headers = [
            "Date",
            "Temperature (°C)",
            "Feels Like (°C)",
            "Min Temp (°C)",
            "Max Temp (°C)",
            "Humidity (%)",
            "Pressure (hPa)",
            "Wind Speed (m/s)",
            "Description",
        ]

        for col_idx, header in enumerate(headers, start=1):
            cell = sheet.cell(row=1, column=col_idx)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = PatternFill(
                start_color="C0C0C0", end_color="C0C0C0", fill_type="solid"
            )

        # Data rows
        for row_idx, wd in enumerate(
            sorted(record.weather_data, key=lambda x: x.forecast_date or ""), start=2
        ):
            sheet.cell(row=row_idx, column=1).value = wd.forecast_date
            sheet.cell(row=row_idx, column=2).value = wd.temperature
            sheet.cell(row=row_idx, column=3).value = wd.feels_like
            sheet.cell(row=row_idx, column=4).value = wd.temp_min
            sheet.cell(row=row_idx, column=5).value = wd.temp_max
            sheet.cell(row=row_idx, column=6).value = wd.humidity
            sheet.cell(row=row_idx, column=7).value = wd.pressure
            sheet.cell(row=row_idx, column=8).value = wd.wind_speed
            sheet.cell(row=row_idx, column=9).value = wd.weather_description

    def _create_youtube_sheet(self, workbook: openpyxl.Workbook, record: WeatherRecord):
        """Create YouTube videos sheet.

        Args:
            workbook: openpyxl Workbook instance
            record: WeatherRecord instance
        """
        sheet = workbook.create_sheet("YouTube Videos")

        # Headers
        headers = ["Title", "Channel", "URL", "Published At"]
        for col_idx, header in enumerate(headers, start=1):
            cell = sheet.cell(row=1, column=col_idx)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = PatternFill(
                start_color="C0C0C0", end_color="C0C0C0", fill_type="solid"
            )

        # Data rows
        for row_idx, yv in enumerate(record.youtube_videos, start=2):
            sheet.cell(row=row_idx, column=1).value = yv.title
            sheet.cell(row=row_idx, column=2).value = yv.channel_title
            sheet.cell(row=row_idx, column=3).value = yv.url
            sheet.cell(row=row_idx, column=4).value = yv.published_at

    def _create_map_sheet(self, workbook: openpyxl.Workbook, record: WeatherRecord):
        """Create map locations sheet.

        Args:
            workbook: openpyxl Workbook instance
            record: WeatherRecord instance
        """
        sheet = workbook.create_sheet("Map Locations")

        # Headers
        headers = ["Address", "Map URL", "Place Type", "Point of Interest"]
        for col_idx, header in enumerate(headers, start=1):
            cell = sheet.cell(row=1, column=col_idx)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = PatternFill(
                start_color="C0C0C0", end_color="C0C0C0", fill_type="solid"
            )

        # Data rows
        for row_idx, ml in enumerate(record.map_locations, start=2):
            sheet.cell(row=row_idx, column=1).value = ml.formatted_address
            sheet.cell(row=row_idx, column=2).value = ml.map_url
            sheet.cell(row=row_idx, column=3).value = ml.place_type
            sheet.cell(row=row_idx, column=4).value = ml.point_of_interest


class ExportManager:
    """Manager to handle all export formats with a unified interface."""

    def __init__(self, db: AsyncSession):
        """Initialize export manager with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def export_to_json(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Export record to JSON format.

        Args:
            record_id: ID of the weather record

        Returns:
            JSON-serializable dictionary
        """
        exporter = JSONExporter(self.db)
        return await exporter.export(record_id)

    async def export_to_csv(self, record_id: int) -> Optional[str]:
        """Export record to CSV format.

        Args:
            record_id: ID of the weather record

        Returns:
            CSV string
        """
        exporter = CSVExporter(self.db)
        return await exporter.export(record_id)

    async def export_to_excel(self, record_id: int) -> Optional[bytes]:
        """Export record to Excel format.

        Args:
            record_id: ID of the weather record

        Returns:
            Excel file as bytes
        """
        exporter = ExcelExporter(self.db)
        return await exporter.export(record_id)

    async def get_export_filename(self, record_id: int, format: str) -> Optional[str]:
        """Generate export filename for a record.

        Args:
            record_id: ID of the weather record
            format: Export format (json, csv, xlsx)

        Returns:
            Filename string, or None if record not found
        """
        exporter = WeatherExporter(self.db)
        record = await exporter.get_record_with_relations(record_id)

        if not record:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_location = "".join(
            c for c in record.location_name if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        safe_location = safe_location.replace(" ", "_")[:50]  # Limit length

        extension_map = {
            "json": "json",
            "csv": "csv",
            "xlsx": "xlsx",
        }

        extension = extension_map.get(format.lower(), "txt")
        return f"weather_{safe_location}_{record_id}_{timestamp}.{extension}"

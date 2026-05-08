"""Export controller - HTTP layer for data export endpoints.

This module contains the controller functions that handle:
- Export requests for weather data in various formats
- Streaming responses for file downloads
- Delegation to export service for business logic
- Uses custom exceptions from app.core.exceptions
"""

import io
import json
import logging
from typing import Optional

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError, WeatherAppException
from app.infrastructure.exporters import REPORTLAB_AVAILABLE, ExportManager
from app.repositories.weather_repository import WeatherRepository
from app.schemas.export import ExportRequest

logger = logging.getLogger(__name__)


async def export_weather_data_controller(
    export_request: ExportRequest,
    db: AsyncSession,
) -> StreamingResponse:
    """Export weather data in specified format.

    Controller logic:
    - Validates export format
    - Delegates to export service
    - Returns streaming response for file download
    """
    try:
        # Initialize export manager
        export_manager = ExportManager(db)

        # Get the record ID from the request
        record_id = export_request.location_id

        if record_id is None:
            # If no location_id provided, get the first available record
            repository = WeatherRepository(db)
            records = await repository.get_all_weather_records(
                skip=0,
                limit=1,
                location_name=None,
            )
            if not records:
                raise NotFoundError(
                    resource="Weather records",
                )
            record_id = records[0].id

        # Generate export based on format
        format_lower = export_request.format.lower()

        # Get filename for the response
        filename = await export_manager.get_export_filename(record_id, format_lower)

        if not filename:
            raise NotFoundError(
                resource="Weather record",
                identifier=record_id,
            )

        # Export data based on format
        if format_lower == "json":
            content = await export_manager.export_to_json(record_id)
            if content is None:
                raise NotFoundError(resource="Weather record", identifier=record_id)
            content_bytes = json.dumps(content, indent=2).encode("utf-8")
            media_type = "application/json"
        elif format_lower == "csv":
            content = await export_manager.export_to_csv(record_id)
            if content is None:
                raise NotFoundError(resource="Weather record", identifier=record_id)
            content_bytes = content.encode("utf-8")
            media_type = "text/csv"
        elif format_lower == "xml":
            content = await export_manager.export_to_xml(record_id)
            if content is None:
                raise NotFoundError(resource="Weather record", identifier=record_id)
            content_bytes = content.encode("utf-8")
            media_type = "application/xml"
        elif format_lower == "pdf":
            content = await export_manager.export_to_pdf(record_id)
            if content is None:
                raise NotFoundError(resource="Weather record", identifier=record_id)
            content_bytes = content
            media_type = "application/pdf"
        elif format_lower == "md" or format_lower == "markdown":
            content = await export_manager.export_to_markdown(record_id)
            if content is None:
                raise NotFoundError(resource="Weather record", identifier=record_id)
            content_bytes = content.encode("utf-8")
            media_type = "text/markdown"
        elif format_lower == "xlsx" or format_lower == "excel":
            content = await export_manager.export_to_excel(record_id)
            if content is None:
                raise NotFoundError(resource="Weather record", identifier=record_id)
            content_bytes = content
            media_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            raise ValidationError(
                message=f"Unsupported export format: {export_request.format}",
            )

        # Create streaming response
        return StreamingResponse(
            io.BytesIO(content_bytes),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise ValidationError(message=str(e))
    except WeatherAppException:
        raise
    except Exception as e:
        logger.error(f"Error exporting weather data: {str(e)}")
        raise WeatherAppException(
            message=f"Failed to export weather data: {str(e)}",
            status_code=500,
            error_code="EXPORT_ERROR",
        )


async def get_export_formats_controller() -> dict:
    """Get available export formats.

    Returns a list of supported export formats with descriptions.
    """
    formats = [
        {
            "format": "json",
            "name": "JSON",
            "description": "JavaScript Object Notation format",
            "content_type": "application/json",
        },
        {
            "format": "csv",
            "name": "CSV",
            "description": "Comma-Separated Values format",
            "content_type": "text/csv",
        },
        {
            "format": "xml",
            "name": "XML",
            "description": "Extensible Markup Language format",
            "content_type": "application/xml",
        },
        {
            "format": "pdf",
            "name": "PDF",
            "description": "Portable Document Format",
            "content_type": "application/pdf",
        },
        {
            "format": "md",
            "name": "Markdown",
            "description": "Markdown text format",
            "content_type": "text/markdown",
        },
        {
            "format": "xlsx",
            "name": "Excel",
            "description": "Microsoft Excel format (XLSX)",
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        },
    ]

    # Check if PDF is available
    if not REPORTLAB_AVAILABLE:
        for fmt in formats:
            if fmt["format"] == "pdf":
                fmt["available"] = False
                fmt["description"] += " (requires reportlab installation)"
                break

    return {"formats": formats}

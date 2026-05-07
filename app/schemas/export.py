from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ExportBase(BaseModel):
    """Base schema for export operations."""

    format: str  # 'csv', 'json', 'xlsx'
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location_id: Optional[int] = None

    @field_validator("format")
    def validate_format(cls, v: str) -> str:
        allowed = ("csv", "json", "xlsx")
        if v not in allowed:
            raise ValueError(f"Format must be one of: {', '.join(allowed)}")
        return v

    @field_validator("end_date")
    def validate_end_date(cls, v: Optional[date], values) -> Optional[date]:
        start_date = values.data.get("start_date")
        if v and start_date and v < start_date:
            raise ValueError("end_date must be on or after start_date")
        return v


class ExportRequest(ExportBase):
    """Schema for export request payload."""

    pass


class ExportResponse(BaseModel):
    """Schema for export response data."""

    id: int
    format: str
    file_url: str
    record_count: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)

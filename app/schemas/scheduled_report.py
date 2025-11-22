from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.scheduled_report import ReportFrequency, ReportFormat


class ScheduledReportCreate(BaseModel):
    name: str
    description: Optional[str] = None
    report_type: str
    frequency: ReportFrequency
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    time_of_day: str = "09:00"
    format: ReportFormat = ReportFormat.PDF
    recipients: List[str]
    filters: Optional[Dict[str, Any]] = None


class ScheduledReportUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[ReportFrequency] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    time_of_day: Optional[str] = None
    format: Optional[ReportFormat] = None
    recipients: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ScheduledReportResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    report_type: str
    frequency: ReportFrequency
    day_of_week: Optional[int]
    day_of_month: Optional[int]
    time_of_day: str
    format: ReportFormat
    recipients: List[str]
    filters: Optional[Dict[str, Any]]
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_by_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReportExecutionResponse(BaseModel):
    id: int
    scheduled_report_id: int
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    error_message: Optional[str]
    file_size: Optional[int]
    recipients_count: int
    sent_successfully: bool

    class Config:
        from_attributes = True

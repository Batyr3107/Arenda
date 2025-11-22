from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class ReportFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class ReportFormat(str, enum.Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class ScheduledReport(Base):
    """Scheduled report configuration"""
    __tablename__ = "scheduled_reports"

    id = Column(Integer, primary_key=True, index=True)

    # Report configuration
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    report_type = Column(String, nullable=False)  # occupancy, revenue, payments, etc.

    # Schedule
    frequency = Column(SQLEnum(ReportFrequency), nullable=False)
    day_of_week = Column(Integer, nullable=True)  # 0-6 for weekly
    day_of_month = Column(Integer, nullable=True)  # 1-31 for monthly
    time_of_day = Column(String, default="09:00")  # HH:MM format

    # Format and delivery
    format = Column(SQLEnum(ReportFormat), default=ReportFormat.PDF)
    recipients = Column(JSON, nullable=False)  # List of email addresses

    # Filters
    filters = Column(JSON, nullable=True)  # Custom filters for the report

    # Status
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)

    # Ownership
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<ScheduledReport {self.name} - {self.frequency.value}>"


class ReportExecution(Base):
    """Log of report executions"""
    __tablename__ = "report_executions"

    id = Column(Integer, primary_key=True, index=True)

    scheduled_report_id = Column(Integer, ForeignKey("scheduled_reports.id"), nullable=False, index=True)

    # Execution details
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False)  # success, failed, running
    error_message = Column(String, nullable=True)

    # Result
    file_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    recipients_count = Column(Integer, default=0)
    sent_successfully = Column(Boolean, default=False)

    # Relationship
    scheduled_report = relationship("ScheduledReport", backref="executions")

    def __repr__(self):
        return f"<ReportExecution {self.id} - {self.status}>"

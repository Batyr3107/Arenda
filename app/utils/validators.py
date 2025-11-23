"""
Validation utilities for common business logic validations
Consolidates scattered validation logic across endpoints
"""
import re
from typing import Optional
from datetime import date, datetime
from fastapi import HTTPException, status


def validate_email(email: str) -> str:
    """
    Validate email format

    Raises:
        HTTPException: 400 if invalid format

    Example:
        email = validate_email(user_data.email)
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

    return email.lower()


def validate_phone(phone: str) -> str:
    """
    Validate phone number (Kazakhstan format or international)

    Raises:
        HTTPException: 400 if invalid format

    Example:
        phone = validate_phone("+77001234567")
    """
    # Remove spaces and dashes
    clean_phone = re.sub(r'[\s\-()]', '', phone)

    # Check if it's a valid format
    # Kazakhstan: +7 (7xx) xxx-xx-xx
    # International: +[country code][number]
    if not re.match(r'^\+?[1-9]\d{9,14}$', clean_phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )

    return clean_phone


def validate_bin_iin(bin_iin: str) -> str:
    """
    Validate Kazakhstan BIN/IIN (12 digits)

    Raises:
        HTTPException: 400 if invalid

    Example:
        bin_iin = validate_bin_iin("123456789012")
    """
    # Remove spaces
    clean_bin_iin = bin_iin.replace(' ', '')

    # Must be exactly 12 digits
    if not re.match(r'^\d{12}$', clean_bin_iin):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BIN/IIN must be 12 digits"
        )

    return clean_bin_iin


def validate_date_range(
    start_date: date,
    end_date: date,
    min_days: Optional[int] = None,
    max_days: Optional[int] = None
) -> tuple[date, date]:
    """
    Validate date range

    Args:
        start_date: Start date
        end_date: End date
        min_days: Minimum number of days between dates
        max_days: Maximum number of days between dates

    Raises:
        HTTPException: 400 if invalid range

    Example:
        start, end = validate_date_range(
            contract.start_date,
            contract.end_date,
            min_days=30  # Contracts must be at least 1 month
        )
    """
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )

    if min_days is not None:
        days_diff = (end_date - start_date).days
        if days_diff < min_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Date range must be at least {min_days} days"
            )

    if max_days is not None:
        days_diff = (end_date - start_date).days
        if days_diff > max_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Date range cannot exceed {max_days} days"
            )

    return start_date, end_date


def validate_amount(
    amount: float,
    min_amount: Optional[float] = 0.0,
    max_amount: Optional[float] = None,
    field_name: str = "Amount"
) -> float:
    """
    Validate monetary amount

    Args:
        amount: Amount to validate
        min_amount: Minimum allowed amount
        max_amount: Maximum allowed amount
        field_name: Name for error messages

    Raises:
        HTTPException: 400 if invalid

    Example:
        rent = validate_amount(
            contract_data.monthly_rent,
            min_amount=1000,
            field_name="Monthly rent"
        )
    """
    if amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be negative"
        )

    if min_amount is not None and amount < min_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be at least {min_amount}"
        )

    if max_amount is not None and amount > max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot exceed {max_amount}"
        )

    return amount


def validate_percentage(
    percentage: float,
    field_name: str = "Percentage"
) -> float:
    """
    Validate percentage (0-100)

    Example:
        late_fee = validate_percentage(
            contract_data.late_fee_percentage,
            "Late fee percentage"
        )
    """
    if not 0 <= percentage <= 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be between 0 and 100"
        )

    return percentage


def validate_payment_day(day: int) -> int:
    """
    Validate payment day of month (1-31)

    Example:
        payment_day = validate_payment_day(contract_data.payment_day)
    """
    if not 1 <= day <= 31:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment day must be between 1 and 31"
        )

    return day


def validate_file_size(
    file_size: int,
    max_size: int = 10485760  # 10MB default
) -> int:
    """
    Validate file size

    Args:
        file_size: File size in bytes
        max_size: Maximum allowed size in bytes

    Raises:
        HTTPException: 400 if too large

    Example:
        validate_file_size(uploaded_file.size)
    """
    if file_size > max_size:
        max_mb = max_size / 1048576
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size cannot exceed {max_mb}MB"
        )

    return file_size


def validate_file_extension(
    filename: str,
    allowed_extensions: list[str]
) -> str:
    """
    Validate file extension

    Args:
        filename: Filename to check
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.jpg'])

    Raises:
        HTTPException: 400 if invalid extension

    Example:
        validate_file_extension(
            file.filename,
            ['.pdf', '.docx', '.txt']
        )
    """
    import os

    ext = os.path.splitext(filename)[1].lower()

    if ext not in [e.lower() for e in allowed_extensions]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {ext} not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )

    return filename


def validate_contract_dates(
    start_date: date,
    end_date: date,
    min_contract_days: int = 30
) -> tuple[date, date]:
    """
    Validate contract date range with business rules

    Args:
        start_date: Contract start date
        end_date: Contract end date
        min_contract_days: Minimum contract duration

    Example:
        start, end = validate_contract_dates(
            contract_data.start_date,
            contract_data.end_date
        )
    """
    # End date must be after start date
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract end date must be after start date"
        )

    # Minimum contract duration
    days = (end_date - start_date).days
    if days < min_contract_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contract must be at least {min_contract_days} days"
        )

    # Start date shouldn't be too far in the past
    if start_date < date.today() - timedelta(days=365):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract start date cannot be more than 1 year in the past"
        )

    return start_date, end_date


def validate_payment_schedule_dates(
    contract_start: date,
    contract_end: date,
    payment_day: int
) -> bool:
    """
    Validate payment schedule parameters

    Example:
        validate_payment_schedule_dates(
            contract.start_date,
            contract.end_date,
            contract.payment_day
        )
    """
    # Payment day must be valid
    validate_payment_day(payment_day)

    # Contract dates must be valid
    if contract_end <= contract_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid contract date range"
        )

    return True


from datetime import timedelta  # Added import for validate_contract_dates

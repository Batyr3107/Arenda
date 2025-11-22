import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException, status
from pathlib import Path
from typing import Optional
from app.core.config import settings


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}


async def save_upload_file(
    file: UploadFile,
    destination: str = "documents",
    allowed_types: Optional[set] = None
) -> tuple[str, int]:
    """
    Save uploaded file and return (file_url, file_size)

    Args:
        file: Uploaded file
        destination: Subfolder in uploads directory
        allowed_types: Set of allowed MIME types

    Returns:
        Tuple of (file_url, file_size in bytes)
    """
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE} bytes"
        )

    # Check MIME type
    if allowed_types and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {allowed_types}"
        )

    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # Create directory if not exists
    upload_dir = Path(settings.UPLOAD_DIR) / destination
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    file_path = upload_dir / unique_filename
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)

    # Return URL relative to upload directory
    file_url = f"/uploads/{destination}/{unique_filename}"
    return file_url, file_size


async def save_premise_photo(file: UploadFile) -> tuple[str, int]:
    """Save premise photo"""
    return await save_upload_file(file, "premises", ALLOWED_IMAGE_TYPES)


async def save_property_photo(file: UploadFile) -> tuple[str, int]:
    """Save property photo"""
    return await save_upload_file(file, "properties", ALLOWED_IMAGE_TYPES)


async def save_payment_document(file: UploadFile) -> tuple[str, int]:
    """Save payment document"""
    return await save_upload_file(file, "payments", ALLOWED_DOCUMENT_TYPES)


async def save_contract_document(file: UploadFile) -> tuple[str, int]:
    """Save contract document"""
    return await save_upload_file(file, "contracts", ALLOWED_DOCUMENT_TYPES)


def delete_file(file_url: str) -> bool:
    """
    Delete file from disk

    Args:
        file_url: URL like /uploads/premises/filename.jpg

    Returns:
        True if deleted, False if not found
    """
    try:
        # Convert URL to file path
        # Remove leading /uploads/ and prepend upload directory
        relative_path = file_url.replace("/uploads/", "")
        file_path = Path(settings.UPLOAD_DIR) / relative_path

        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception:
        return False

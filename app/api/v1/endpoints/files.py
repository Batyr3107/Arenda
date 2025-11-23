from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import List, Callable, Awaitable, Tuple
from app.models.user import User
from app.api.deps import get_moderator_or_higher
from app.utils.file_upload import (
    save_premise_photo,
    save_property_photo,
    save_contract_document,
    delete_file
)

router = APIRouter()


async def _upload_multiple_photos(
    files: List[UploadFile],
    save_func: Callable[[UploadFile], Awaitable[Tuple[str, int]]]
) -> dict:
    """Generic helper for uploading multiple photos
    Eliminates duplication between premise and property photo uploads"""
    uploaded_files = []

    for file in files:
        try:
            file_url, file_size = await save_func(file)
            uploaded_files.append({
                "filename": file.filename,
                "url": file_url,
                "size": file_size
            })
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error uploading {file.filename}: {str(e)}"
            )

    return {"uploaded": uploaded_files}


@router.post("/premises/photos")
async def upload_premise_photos(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Upload multiple photos for a premise
    Refactored: Using generic upload helper"""
    return await _upload_multiple_photos(files, save_premise_photo)


@router.post("/properties/photos")
async def upload_property_photos(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Upload multiple photos for a property
    Refactored: Using generic upload helper"""
    return await _upload_multiple_photos(files, save_property_photo)


@router.post("/contracts/documents")
async def upload_contract_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Upload contract document"""
    try:
        file_url, file_size = await save_contract_document(file)
        return {
            "filename": file.filename,
            "url": file_url,
            "size": file_size
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error uploading file: {str(e)}"
        )


@router.delete("/delete")
async def delete_uploaded_file(
    file_url: str,
    current_user: User = Depends(get_moderator_or_higher)
):
    """Delete uploaded file"""
    success = delete_file(file_url)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return {"message": "File deleted successfully"}

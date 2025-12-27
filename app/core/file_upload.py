"""File upload utilities"""
import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.core.config import settings


ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg'}


def validate_image_file(file: UploadFile) -> None:
    """
    Validate image file format and size.
    
    Args:
        file: The uploaded file
        
    Raises:
        HTTPException: If validation fails
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower() if file.filename else ''
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Only PNG and JPG files are allowed."
        )
    
    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only PNG and JPG images are allowed."
        )


async def save_uploaded_image(file: UploadFile) -> str:
    """
    Save an uploaded image file and return the file path.
    
    Args:
        file: The uploaded file
        
    Returns:
        The relative path to the saved file
        
    Raises:
        HTTPException: If validation or save fails
    """
    # Validate the file
    validate_image_file(file)
    
    # Read file content to check size
    content = await file.read()
    file_size = len(content)
    
    # Validate file size
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE / (1024 * 1024):.1f}MB"
        )
    
    # Reset file pointer
    await file.seek(0)
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix.lower() if file.filename else '.jpg'
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Ensure upload directory exists
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = upload_dir / unique_filename
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Return relative path
    return f"/uploads/{unique_filename}"


def delete_uploaded_file(file_path: str) -> bool:
    """
    Delete an uploaded file.
    
    Args:
        file_path: The relative path to the file
        
    Returns:
        True if file was deleted, False otherwise
    """
    try:
        # Extract filename from path
        filename = Path(file_path).name
        full_path = Path(settings.UPLOAD_DIR) / filename
        
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    except Exception:
        return False

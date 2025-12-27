"""Painter API endpoints"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.painter import PainterService
from app.schemas.painter import PainterCreate, PainterUpdate, PainterResponse

router = APIRouter(prefix="/api/painters", tags=["Painters"])


@router.post("", response_model=PainterResponse, status_code=status.HTTP_201_CREATED)
def create_painter(
    painter_data: PainterCreate,
    db: Session = Depends(get_db)
):
    """Create a new painter"""
    service = PainterService(db)
    return service.create_painter(painter_data)


@router.get("", response_model=List[PainterResponse])
def get_painters(db: Session = Depends(get_db)):
    """Get all painters"""
    service = PainterService(db)
    return service.get_all_painters()


@router.get("/{painter_id}", response_model=PainterResponse)
def get_painter(painter_id: str, db: Session = Depends(get_db)):
    """Get a painter by ID"""
    service = PainterService(db)
    return service.get_painter(painter_id)


@router.put("/{painter_id}", response_model=PainterResponse)
def update_painter(
    painter_id: str,
    painter_data: PainterUpdate,
    db: Session = Depends(get_db)
):
    """Update a painter"""
    service = PainterService(db)
    return service.update_painter(painter_id, painter_data)


@router.delete("/{painter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_painter(painter_id: str, db: Session = Depends(get_db)):
    """Delete a painter"""
    service = PainterService(db)
    service.delete_painter(painter_id)

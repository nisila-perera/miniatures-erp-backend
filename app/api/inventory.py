"""Inventory API endpoints"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.inventory import ResinService, PaintBottleService
from app.schemas.inventory import (
    ResinCreate, ResinUpdate, ResinResponse,
    PaintBottleCreate, PaintBottleUpdate, PaintBottleResponse
)

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


# Resin endpoints
@router.post("/resin", response_model=ResinResponse, status_code=status.HTTP_201_CREATED)
def create_resin(
    resin_data: ResinCreate,
    db: Session = Depends(get_db)
):
    """Create a new resin entry"""
    service = ResinService(db)
    return service.create_resin(resin_data)


@router.get("/resin", response_model=List[ResinResponse])
def get_all_resin(db: Session = Depends(get_db)):
    """Get all resin entries"""
    service = ResinService(db)
    return service.get_all_resin()


@router.get("/resin/{resin_id}", response_model=ResinResponse)
def get_resin(resin_id: str, db: Session = Depends(get_db)):
    """Get a resin entry by ID"""
    service = ResinService(db)
    return service.get_resin(resin_id)


@router.put("/resin/{resin_id}", response_model=ResinResponse)
def update_resin(
    resin_id: str,
    resin_data: ResinUpdate,
    db: Session = Depends(get_db)
):
    """Update a resin entry"""
    service = ResinService(db)
    return service.update_resin(resin_id, resin_data)


@router.delete("/resin/{resin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resin(resin_id: str, db: Session = Depends(get_db)):
    """Delete a resin entry"""
    service = ResinService(db)
    service.delete_resin(resin_id)


# Paint bottle endpoints
@router.post("/paint", response_model=PaintBottleResponse, status_code=status.HTTP_201_CREATED)
def create_paint_bottle(
    paint_data: PaintBottleCreate,
    db: Session = Depends(get_db)
):
    """Create a new paint bottle entry"""
    service = PaintBottleService(db)
    return service.create_paint_bottle(paint_data)


@router.get("/paint", response_model=List[PaintBottleResponse])
def get_all_paint_bottles(db: Session = Depends(get_db)):
    """Get all paint bottle entries"""
    service = PaintBottleService(db)
    return service.get_all_paint_bottles()


@router.get("/paint/{paint_id}", response_model=PaintBottleResponse)
def get_paint_bottle(paint_id: str, db: Session = Depends(get_db)):
    """Get a paint bottle entry by ID"""
    service = PaintBottleService(db)
    return service.get_paint_bottle(paint_id)


@router.put("/paint/{paint_id}", response_model=PaintBottleResponse)
def update_paint_bottle(
    paint_id: str,
    paint_data: PaintBottleUpdate,
    db: Session = Depends(get_db)
):
    """Update a paint bottle entry"""
    service = PaintBottleService(db)
    return service.update_paint_bottle(paint_id, paint_data)


@router.delete("/paint/{paint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paint_bottle(paint_id: str, db: Session = Depends(get_db)):
    """Delete a paint bottle entry"""
    service = PaintBottleService(db)
    service.delete_paint_bottle(paint_id)

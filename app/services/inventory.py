"""Inventory service for business logic"""
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.inventory import ResinRepository, PaintBottleRepository
from app.schemas.inventory import (
    ResinCreate, ResinUpdate, ResinResponse,
    PaintBottleCreate, PaintBottleUpdate, PaintBottleResponse
)


class ResinService:
    """Service for resin business logic"""
    
    def __init__(self, db: Session):
        self.repository = ResinRepository(db)
    
    def create_resin(self, resin_data: ResinCreate) -> ResinResponse:
        """Create a new resin entry"""
        # Validate that color is not empty
        if not resin_data.color or not resin_data.color.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resin color cannot be empty"
            )
        
        resin = self.repository.create(resin_data)
        return ResinResponse.model_validate(resin)
    
    def get_resin(self, resin_id: str) -> ResinResponse:
        """Get a resin entry by ID"""
        resin = self.repository.get_by_id(resin_id)
        if not resin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resin with id {resin_id} not found"
            )
        return ResinResponse.model_validate(resin)
    
    def get_all_resin(self) -> List[ResinResponse]:
        """Get all resin entries"""
        resins = self.repository.get_all()
        return [ResinResponse.model_validate(resin) for resin in resins]
    
    def update_resin(self, resin_id: str, resin_data: ResinUpdate) -> ResinResponse:
        """Update a resin entry"""
        # Check if resin exists
        resin = self.repository.get_by_id(resin_id)
        if not resin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resin with id {resin_id} not found"
            )
        
        # Validate that color is not empty if provided
        if resin_data.color is not None and (not resin_data.color or not resin_data.color.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resin color cannot be empty"
            )
        
        updated_resin = self.repository.update(resin_id, resin_data)
        return ResinResponse.model_validate(updated_resin)
    
    def delete_resin(self, resin_id: str) -> None:
        """Delete a resin entry"""
        success = self.repository.delete(resin_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resin with id {resin_id} not found"
            )


class PaintBottleService:
    """Service for paint bottle business logic"""
    
    def __init__(self, db: Session):
        self.repository = PaintBottleRepository(db)
    
    def create_paint_bottle(self, paint_data: PaintBottleCreate) -> PaintBottleResponse:
        """Create a new paint bottle entry"""
        # Validate that color is not empty
        if not paint_data.color or not paint_data.color.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Paint bottle color cannot be empty"
            )
        
        # Validate that brand is not empty
        if not paint_data.brand or not paint_data.brand.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Paint bottle brand cannot be empty"
            )
        
        # Validate that current_volume_ml does not exceed volume_ml
        if paint_data.current_volume_ml > paint_data.volume_ml:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current volume cannot exceed total volume"
            )
        
        paint = self.repository.create(paint_data)
        return PaintBottleResponse.model_validate(paint)
    
    def get_paint_bottle(self, paint_id: str) -> PaintBottleResponse:
        """Get a paint bottle entry by ID"""
        paint = self.repository.get_by_id(paint_id)
        if not paint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paint bottle with id {paint_id} not found"
            )
        return PaintBottleResponse.model_validate(paint)
    
    def get_all_paint_bottles(self) -> List[PaintBottleResponse]:
        """Get all paint bottle entries"""
        paints = self.repository.get_all()
        return [PaintBottleResponse.model_validate(paint) for paint in paints]
    
    def update_paint_bottle(self, paint_id: str, paint_data: PaintBottleUpdate) -> PaintBottleResponse:
        """Update a paint bottle entry"""
        # Check if paint bottle exists
        paint = self.repository.get_by_id(paint_id)
        if not paint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paint bottle with id {paint_id} not found"
            )
        
        # Validate that color is not empty if provided
        if paint_data.color is not None and (not paint_data.color or not paint_data.color.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Paint bottle color cannot be empty"
            )
        
        # Validate that brand is not empty if provided
        if paint_data.brand is not None and (not paint_data.brand or not paint_data.brand.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Paint bottle brand cannot be empty"
            )
        
        # Validate that current_volume_ml does not exceed volume_ml if both are provided
        volume_ml = paint_data.volume_ml if paint_data.volume_ml is not None else paint.volume_ml
        current_volume_ml = paint_data.current_volume_ml if paint_data.current_volume_ml is not None else paint.current_volume_ml
        
        if current_volume_ml > volume_ml:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current volume cannot exceed total volume"
            )
        
        updated_paint = self.repository.update(paint_id, paint_data)
        return PaintBottleResponse.model_validate(updated_paint)
    
    def delete_paint_bottle(self, paint_id: str) -> None:
        """Delete a paint bottle entry"""
        success = self.repository.delete(paint_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paint bottle with id {paint_id} not found"
            )

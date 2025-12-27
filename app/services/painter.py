"""Painter service for business logic"""
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.painter import PainterRepository
from app.schemas.painter import PainterCreate, PainterUpdate, PainterResponse


class PainterService:
    """Service for painter business logic"""
    
    def __init__(self, db: Session):
        self.repository = PainterRepository(db)
    
    def create_painter(self, painter_data: PainterCreate) -> PainterResponse:
        """Create a new painter"""
        # Validate that name is not empty
        if not painter_data.name or not painter_data.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Painter name cannot be empty"
            )
        
        painter = self.repository.create(painter_data)
        return PainterResponse.model_validate(painter)
    
    def get_painter(self, painter_id: str) -> PainterResponse:
        """Get a painter by ID"""
        painter = self.repository.get_by_id(painter_id)
        if not painter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Painter with id {painter_id} not found"
            )
        return PainterResponse.model_validate(painter)
    
    def get_all_painters(self) -> List[PainterResponse]:
        """Get all painters"""
        painters = self.repository.get_all()
        return [PainterResponse.model_validate(painter) for painter in painters]
    
    def update_painter(self, painter_id: str, painter_data: PainterUpdate) -> PainterResponse:
        """Update a painter"""
        # Get the painter first to check if it exists
        painter = self.repository.get_by_id(painter_id)
        if not painter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Painter with id {painter_id} not found"
            )
        
        # Validate that name is not empty if provided
        if painter_data.name is not None and (not painter_data.name or not painter_data.name.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Painter name cannot be empty"
            )
        
        updated_painter = self.repository.update(painter_id, painter_data)
        return PainterResponse.model_validate(updated_painter)
    
    def delete_painter(self, painter_id: str) -> None:
        """Delete a painter"""
        painter = self.repository.get_by_id(painter_id)
        if not painter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Painter with id {painter_id} not found"
            )
        
        success = self.repository.delete(painter_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Painter with id {painter_id} not found"
            )

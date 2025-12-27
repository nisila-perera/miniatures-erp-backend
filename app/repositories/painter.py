"""Painter repository for database operations"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.painter import Painter
from app.schemas.painter import PainterCreate, PainterUpdate


class PainterRepository:
    """Repository for painter database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, painter_data: PainterCreate) -> Painter:
        """Create a new painter"""
        painter = Painter(**painter_data.model_dump())
        self.db.add(painter)
        self.db.commit()
        self.db.refresh(painter)
        return painter
    
    def get_by_id(self, painter_id: str) -> Optional[Painter]:
        """Get a painter by ID"""
        return self.db.query(Painter).filter(Painter.id == painter_id).first()
    
    def get_all(self) -> List[Painter]:
        """Get all painters"""
        return self.db.query(Painter).all()
    
    def update(self, painter_id: str, painter_data: PainterUpdate) -> Optional[Painter]:
        """Update a painter"""
        painter = self.get_by_id(painter_id)
        if not painter:
            return None
        
        update_data = painter_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(painter, field, value)
        
        self.db.commit()
        self.db.refresh(painter)
        return painter
    
    def delete(self, painter_id: str) -> bool:
        """Delete a painter"""
        painter = self.get_by_id(painter_id)
        if not painter:
            return False
        
        self.db.delete(painter)
        self.db.commit()
        return True

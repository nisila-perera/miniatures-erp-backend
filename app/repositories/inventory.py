"""Inventory repository for database operations"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.inventory import Resin, PaintBottle
from app.schemas.inventory import ResinCreate, ResinUpdate, PaintBottleCreate, PaintBottleUpdate


class ResinRepository:
    """Repository for resin database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, resin_data: ResinCreate) -> Resin:
        """Create a new resin entry"""
        resin = Resin(**resin_data.model_dump())
        self.db.add(resin)
        self.db.commit()
        self.db.refresh(resin)
        return resin
    
    def get_by_id(self, resin_id: str) -> Optional[Resin]:
        """Get a resin entry by ID"""
        return self.db.query(Resin).filter(Resin.id == resin_id).first()
    
    def get_all(self) -> List[Resin]:
        """Get all resin entries"""
        return self.db.query(Resin).all()
    
    def update(self, resin_id: str, resin_data: ResinUpdate) -> Optional[Resin]:
        """Update a resin entry"""
        resin = self.get_by_id(resin_id)
        if not resin:
            return None
        
        update_data = resin_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(resin, field, value)
        
        self.db.commit()
        self.db.refresh(resin)
        return resin
    
    def delete(self, resin_id: str) -> bool:
        """Delete a resin entry"""
        resin = self.get_by_id(resin_id)
        if not resin:
            return False
        
        self.db.delete(resin)
        self.db.commit()
        return True


class PaintBottleRepository:
    """Repository for paint bottle database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, paint_data: PaintBottleCreate) -> PaintBottle:
        """Create a new paint bottle entry"""
        paint = PaintBottle(**paint_data.model_dump())
        self.db.add(paint)
        self.db.commit()
        self.db.refresh(paint)
        return paint
    
    def get_by_id(self, paint_id: str) -> Optional[PaintBottle]:
        """Get a paint bottle entry by ID"""
        return self.db.query(PaintBottle).filter(PaintBottle.id == paint_id).first()
    
    def get_all(self) -> List[PaintBottle]:
        """Get all paint bottle entries"""
        return self.db.query(PaintBottle).all()
    
    def update(self, paint_id: str, paint_data: PaintBottleUpdate) -> Optional[PaintBottle]:
        """Update a paint bottle entry"""
        paint = self.get_by_id(paint_id)
        if not paint:
            return None
        
        update_data = paint_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(paint, field, value)
        
        self.db.commit()
        self.db.refresh(paint)
        return paint
    
    def delete(self, paint_id: str) -> bool:
        """Delete a paint bottle entry"""
        paint = self.get_by_id(paint_id)
        if not paint:
            return False
        
        self.db.delete(paint)
        self.db.commit()
        return True

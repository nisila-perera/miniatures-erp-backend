"""Product category repository for database operations"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.product import ProductCategory
from app.schemas.product import ProductCategoryCreate, ProductCategoryUpdate


class ProductCategoryRepository:
    """Repository for product category database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, category_data: ProductCategoryCreate) -> ProductCategory:
        """Create a new product category"""
        category = ProductCategory(**category_data.model_dump())
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def get_by_id(self, category_id: str) -> Optional[ProductCategory]:
        """Get a product category by ID"""
        return self.db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
    
    def get_all(self) -> List[ProductCategory]:
        """Get all product categories"""
        return self.db.query(ProductCategory).all()
    
    def update(self, category_id: str, category_data: ProductCategoryUpdate) -> Optional[ProductCategory]:
        """Update a product category"""
        category = self.get_by_id(category_id)
        if not category:
            return None
        
        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def delete(self, category_id: str) -> bool:
        """Delete a product category"""
        category = self.get_by_id(category_id)
        if not category:
            return False
        
        self.db.delete(category)
        self.db.commit()
        return True
    
    def get_by_name(self, name: str) -> Optional[ProductCategory]:
        """Get a product category by name"""
        return self.db.query(ProductCategory).filter(ProductCategory.name == name).first()

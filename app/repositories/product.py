"""Product repository for database operations"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.enums import ProductSource
from app.schemas.product import ProductCreate, ProductUpdate


class ProductRepository:
    """Repository for product database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, product_data: ProductCreate) -> Product:
        """Create a new product"""
        product = Product(**product_data.model_dump())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def get_by_id(self, product_id: str) -> Optional[Product]:
        """Get a product by ID"""
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    def get_all(self) -> List[Product]:
        """Get all products"""
        return self.db.query(Product).all()
    
    def update(self, product_id: str, product_data: ProductUpdate) -> Optional[Product]:
        """Update a product"""
        product = self.get_by_id(product_id)
        if not product:
            return None
        
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def delete(self, product_id: str) -> bool:
        """Delete a product"""
        product = self.get_by_id(product_id)
        if not product:
            return False
        
        self.db.delete(product)
        self.db.commit()
        return True
    
    def get_by_woocommerce_id(self, woocommerce_id: int) -> Optional[Product]:
        """Get a product by WooCommerce ID"""
        return self.db.query(Product).filter(Product.woocommerce_id == woocommerce_id).first()

"""Product and ProductCategory models"""
from sqlalchemy import Column, String, Numeric, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_uuid
from app.models.enums import ProductSource


class ProductCategory(Base, TimestampMixin):
    """Product category model"""
    __tablename__ = "product_categories"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    
    # Relationships
    products = relationship("Product", back_populates="category")


class Product(Base, TimestampMixin):
    """Product model"""
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(String(2000))
    category_id = Column(UUID(as_uuid=False), ForeignKey("product_categories.id"), nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    is_colored = Column(Boolean, default=False)
    dimensions = Column(String(255))
    source = Column(ENUM(ProductSource, name="product_source"), nullable=False, default=ProductSource.ERP)
    woocommerce_id = Column(Integer)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    category = relationship("ProductCategory", back_populates="products")

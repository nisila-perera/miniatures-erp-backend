"""Product and ProductCategory schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from app.schemas.base import BaseSchema, TimestampSchema
from app.models.enums import ProductSource


class ProductCategoryCreate(BaseModel):
    """Schema for creating a product category"""
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class ProductCategoryUpdate(BaseModel):
    """Schema for updating a product category"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class ProductCategoryResponse(BaseSchema, TimestampSchema):
    """Schema for product category response"""
    id: str
    name: str
    description: Optional[str]


class ProductCreate(BaseModel):
    """Schema for creating a product"""
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category_id: str
    base_price: Decimal = Field(..., ge=0)
    is_colored: bool = False
    dimensions: Optional[str] = Field(None, max_length=255)
    source: ProductSource = ProductSource.ERP
    woocommerce_id: Optional[int] = None
    is_active: bool = True


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category_id: Optional[str] = None
    base_price: Optional[Decimal] = Field(None, ge=0)
    is_colored: Optional[bool] = None
    dimensions: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class ProductResponse(BaseSchema, TimestampSchema):
    """Schema for product response"""
    id: str
    name: str
    description: Optional[str]
    category_id: str
    base_price: Decimal
    is_colored: bool
    dimensions: Optional[str]
    source: ProductSource
    woocommerce_id: Optional[int]
    is_active: bool

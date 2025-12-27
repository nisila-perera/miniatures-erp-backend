"""Product category API endpoints"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.product_category import ProductCategoryService
from app.schemas.product import ProductCategoryCreate, ProductCategoryUpdate, ProductCategoryResponse

router = APIRouter(prefix="/api/product-categories", tags=["Product Categories"])


@router.post("", response_model=ProductCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_product_category(
    category_data: ProductCategoryCreate,
    db: Session = Depends(get_db)
):
    """Create a new product category"""
    service = ProductCategoryService(db)
    return service.create_category(category_data)


@router.get("", response_model=List[ProductCategoryResponse])
def get_product_categories(db: Session = Depends(get_db)):
    """Get all product categories"""
    service = ProductCategoryService(db)
    return service.get_all_categories()


@router.get("/{category_id}", response_model=ProductCategoryResponse)
def get_product_category(category_id: str, db: Session = Depends(get_db)):
    """Get a product category by ID"""
    service = ProductCategoryService(db)
    return service.get_category(category_id)


@router.put("/{category_id}", response_model=ProductCategoryResponse)
def update_product_category(
    category_id: str,
    category_data: ProductCategoryUpdate,
    db: Session = Depends(get_db)
):
    """Update a product category"""
    service = ProductCategoryService(db)
    return service.update_category(category_id, category_data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_category(category_id: str, db: Session = Depends(get_db)):
    """Delete a product category"""
    service = ProductCategoryService(db)
    service.delete_category(category_id)

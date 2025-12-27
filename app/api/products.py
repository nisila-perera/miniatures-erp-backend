"""Product API endpoints"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.product import ProductService
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    """Create a new product"""
    service = ProductService(db)
    return service.create_product(product_data)


@router.get("", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    """Get all products"""
    service = ProductService(db)
    return service.get_all_products()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """Get a product by ID"""
    service = ProductService(db)
    return service.get_product(product_id)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: str,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update a product (ERP products only)"""
    service = ProductService(db)
    return service.update_product(product_id, product_data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, db: Session = Depends(get_db)):
    """Delete a product (ERP products only)"""
    service = ProductService(db)
    service.delete_product(product_id)

"""Product service for business logic"""
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.product import ProductRepository
from app.repositories.product_category import ProductCategoryRepository
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.models.enums import ProductSource


class ProductService:
    """Service for product business logic"""
    
    def __init__(self, db: Session):
        self.repository = ProductRepository(db)
        self.category_repository = ProductCategoryRepository(db)
    
    def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """Create a new product"""
        # Validate that name is not empty
        if not product_data.name or not product_data.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product name cannot be empty"
            )
        
        # Validate that category exists
        category = self.category_repository.get_by_id(product_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product category with id {product_data.category_id} not found"
            )
        
        # Validate that base_price is positive
        if product_data.base_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Base price must be non-negative"
            )
        
        product = self.repository.create(product_data)
        return ProductResponse.model_validate(product)
    
    def get_product(self, product_id: str) -> ProductResponse:
        """Get a product by ID"""
        product = self.repository.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )
        return ProductResponse.model_validate(product)
    
    def get_all_products(self) -> List[ProductResponse]:
        """Get all products"""
        products = self.repository.get_all()
        return [ProductResponse.model_validate(prod) for prod in products]
    
    def update_product(self, product_id: str, product_data: ProductUpdate) -> ProductResponse:
        """Update a product"""
        # Get the product first to check if it exists and its source
        product = self.repository.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )
        
        # Enforce read-only for WooCommerce products
        if product.source == ProductSource.WOOCOMMERCE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update WooCommerce products. They are read-only."
            )
        
        # Validate that name is not empty if provided
        if product_data.name is not None and (not product_data.name or not product_data.name.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product name cannot be empty"
            )
        
        # Validate that category exists if provided
        if product_data.category_id is not None:
            category = self.category_repository.get_by_id(product_data.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product category with id {product_data.category_id} not found"
                )
        
        # Validate that base_price is positive if provided
        if product_data.base_price is not None and product_data.base_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Base price must be non-negative"
            )
        
        updated_product = self.repository.update(product_id, product_data)
        return ProductResponse.model_validate(updated_product)
    
    def delete_product(self, product_id: str) -> None:
        """Delete a product"""
        # Get the product first to check if it exists and its source
        product = self.repository.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )
        
        # Enforce read-only for WooCommerce products
        if product.source == ProductSource.WOOCOMMERCE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete WooCommerce products. They are read-only."
            )
        
        success = self.repository.delete(product_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )

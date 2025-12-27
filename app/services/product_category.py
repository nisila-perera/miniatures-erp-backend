"""Product category service for business logic"""
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.product_category import ProductCategoryRepository
from app.schemas.product import ProductCategoryCreate, ProductCategoryUpdate, ProductCategoryResponse


class ProductCategoryService:
    """Service for product category business logic"""
    
    def __init__(self, db: Session):
        self.repository = ProductCategoryRepository(db)
    
    def create_category(self, category_data: ProductCategoryCreate) -> ProductCategoryResponse:
        """Create a new product category"""
        # Validate that name is not empty
        if not category_data.name or not category_data.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name cannot be empty"
            )
        
        category = self.repository.create(category_data)
        return ProductCategoryResponse.model_validate(category)
    
    def get_category(self, category_id: str) -> ProductCategoryResponse:
        """Get a product category by ID"""
        category = self.repository.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product category with id {category_id} not found"
            )
        return ProductCategoryResponse.model_validate(category)
    
    def get_all_categories(self) -> List[ProductCategoryResponse]:
        """Get all product categories"""
        categories = self.repository.get_all()
        return [ProductCategoryResponse.model_validate(cat) for cat in categories]
    
    def update_category(self, category_id: str, category_data: ProductCategoryUpdate) -> ProductCategoryResponse:
        """Update a product category"""
        # Validate that name is not empty if provided
        if category_data.name is not None and (not category_data.name or not category_data.name.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name cannot be empty"
            )
        
        category = self.repository.update(category_id, category_data)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product category with id {category_id} not found"
            )
        return ProductCategoryResponse.model_validate(category)
    
    def delete_category(self, category_id: str) -> None:
        """Delete a product category"""
        success = self.repository.delete(category_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product category with id {category_id} not found"
            )

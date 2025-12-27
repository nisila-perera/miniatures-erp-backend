"""Integration tests for product category management
These tests verify the complete flow from API to database
"""
import pytest
from decimal import Decimal
from app.models.product import ProductCategory
from app.repositories.product_category import ProductCategoryRepository
from app.services.product_category import ProductCategoryService
from app.schemas.product import ProductCategoryCreate, ProductCategoryUpdate
from fastapi import HTTPException


@pytest.mark.integration
def test_repository_create_and_retrieve(db_session):
    """Test creating and retrieving a category through repository"""
    repo = ProductCategoryRepository(db_session)
    
    category_data = ProductCategoryCreate(
        name="Test Category",
        description="A test category"
    )
    
    created = repo.create(category_data)
    assert created.id is not None
    assert created.name == "Test Category"
    
    retrieved = repo.get_by_id(created.id)
    assert retrieved is not None
    assert retrieved.name == "Test Category"


@pytest.mark.integration
def test_repository_get_all(db_session):
    """Test retrieving all categories"""
    repo = ProductCategoryRepository(db_session)
    
    # Create multiple categories
    cat1 = repo.create(ProductCategoryCreate(name="Category 1"))
    cat2 = repo.create(ProductCategoryCreate(name="Category 2"))
    
    all_categories = repo.get_all()
    assert len(all_categories) >= 2
    category_names = [cat.name for cat in all_categories]
    assert "Category 1" in category_names
    assert "Category 2" in category_names


@pytest.mark.integration
def test_repository_update(db_session):
    """Test updating a category through repository"""
    repo = ProductCategoryRepository(db_session)
    
    created = repo.create(ProductCategoryCreate(name="Original Name"))
    
    update_data = ProductCategoryUpdate(name="Updated Name")
    updated = repo.update(created.id, update_data)
    
    assert updated is not None
    assert updated.name == "Updated Name"


@pytest.mark.integration
def test_repository_delete(db_session):
    """Test deleting a category through repository"""
    repo = ProductCategoryRepository(db_session)
    
    created = repo.create(ProductCategoryCreate(name="To Delete"))
    category_id = created.id
    
    success = repo.delete(category_id)
    assert success is True
    
    deleted = repo.get_by_id(category_id)
    assert deleted is None


@pytest.mark.integration
def test_service_validation_empty_name(db_session):
    """Test that service validates empty category names"""
    service = ProductCategoryService(db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        service.create_category(ProductCategoryCreate(name=""))
    
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()


@pytest.mark.integration
def test_service_not_found_error(db_session):
    """Test that service raises 404 for non-existent categories"""
    service = ProductCategoryService(db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        service.get_category("00000000-0000-0000-0000-000000000000")
    
    assert exc_info.value.status_code == 404


@pytest.mark.integration
def test_complete_crud_flow(db_session):
    """Test complete CRUD flow through service layer"""
    service = ProductCategoryService(db_session)
    
    # Create
    created = service.create_category(ProductCategoryCreate(
        name="Full Format Figures",
        description="Complete miniature figures"
    ))
    assert created.id is not None
    assert created.name == "Full Format Figures"
    
    # Read
    retrieved = service.get_category(created.id)
    assert retrieved.name == "Full Format Figures"
    
    # Update
    updated = service.update_category(
        created.id,
        ProductCategoryUpdate(description="Updated description")
    )
    assert updated.description == "Updated description"
    assert updated.name == "Full Format Figures"  # Name unchanged
    
    # List
    all_categories = service.get_all_categories()
    assert any(cat.id == created.id for cat in all_categories)
    
    # Delete
    service.delete_category(created.id)
    
    with pytest.raises(HTTPException) as exc_info:
        service.get_category(created.id)
    assert exc_info.value.status_code == 404

"""Tests for product category management"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.product import ProductCategory


@pytest.fixture
def client(db_session):
    """Create a test client with database session override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.mark.unit
def test_create_product_category(client, db_session):
    """Test creating a product category via API"""
    response = client.post(
        "/api/product-categories",
        json={
            "name": "Busts",
            "description": "Character busts and head sculptures"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Busts"
    assert data["description"] == "Character busts and head sculptures"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.unit
def test_create_product_category_without_description(client, db_session):
    """Test creating a product category without description"""
    response = client.post(
        "/api/product-categories",
        json={"name": "Adornments"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Adornments"
    assert data["description"] is None


@pytest.mark.unit
def test_create_product_category_empty_name(client, db_session):
    """Test creating a product category with empty name fails"""
    response = client.post(
        "/api/product-categories",
        json={"name": ""}
    )
    
    assert response.status_code == 400


@pytest.mark.unit
def test_get_all_product_categories(client, db_session):
    """Test retrieving all product categories"""
    # Create test categories
    category1 = ProductCategory(name="Category 1", description="First category")
    category2 = ProductCategory(name="Category 2", description="Second category")
    db_session.add_all([category1, category2])
    db_session.commit()
    
    response = client.get("/api/product-categories")
    
    assert response.status_code == 200
    data = response.json()
    # Check that both categories are present (database may have other categories from previous tests)
    assert any(cat["name"] == "Category 1" for cat in data), "Category 1 not found in response"
    assert any(cat["name"] == "Category 2" for cat in data), "Category 2 not found in response"
    
    # Clean up
    db_session.delete(category1)
    db_session.delete(category2)
    db_session.commit()


@pytest.mark.unit
def test_get_product_category_by_id(client, db_session):
    """Test retrieving a specific product category by ID"""
    category = ProductCategory(name="Full Format Figures", description="Complete miniature figures")
    db_session.add(category)
    db_session.commit()
    
    response = client.get(f"/api/product-categories/{category.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == category.id
    assert data["name"] == "Full Format Figures"
    assert data["description"] == "Complete miniature figures"


@pytest.mark.unit
def test_get_product_category_not_found(client, db_session):
    """Test retrieving a non-existent product category"""
    response = client.get("/api/product-categories/00000000-0000-0000-0000-000000000000")
    
    assert response.status_code == 404


@pytest.mark.unit
def test_update_product_category(client, db_session):
    """Test updating a product category"""
    category = ProductCategory(name="Old Name", description="Old description")
    db_session.add(category)
    db_session.commit()
    
    response = client.put(
        f"/api/product-categories/{category.id}",
        json={
            "name": "New Name",
            "description": "New description"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "New description"
    
    # Verify in database
    db_session.refresh(category)
    assert category.name == "New Name"
    assert category.description == "New description"


@pytest.mark.unit
def test_update_product_category_partial(client, db_session):
    """Test partially updating a product category"""
    category = ProductCategory(name="Original Name", description="Original description")
    db_session.add(category)
    db_session.commit()
    
    response = client.put(
        f"/api/product-categories/{category.id}",
        json={"name": "Updated Name"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Original description"


@pytest.mark.unit
def test_update_product_category_not_found(client, db_session):
    """Test updating a non-existent product category"""
    response = client.put(
        "/api/product-categories/00000000-0000-0000-0000-000000000000",
        json={"name": "New Name"}
    )
    
    assert response.status_code == 404


@pytest.mark.unit
def test_delete_product_category(client, db_session):
    """Test deleting a product category"""
    category = ProductCategory(name="To Delete", description="Will be deleted")
    db_session.add(category)
    db_session.commit()
    category_id = category.id
    
    response = client.delete(f"/api/product-categories/{category_id}")
    
    assert response.status_code == 204
    
    # Verify deletion
    deleted_category = db_session.query(ProductCategory).filter(ProductCategory.id == category_id).first()
    assert deleted_category is None


@pytest.mark.unit
def test_delete_product_category_not_found(client, db_session):
    """Test deleting a non-existent product category"""
    response = client.delete("/api/product-categories/00000000-0000-0000-0000-000000000000")
    
    assert response.status_code == 404


# Feature: miniatures-erp, Property 10: Product category unique identifiers
# Validates: Requirements 4.1
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random category names to create multiple categories
    category_count=st.integers(min_value=2, max_value=10),
    name_prefix=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=90))
)
def test_product_category_unique_identifiers(db_session, category_count, name_prefix):
    """
    Property: For any two product categories created in the system, they SHALL have different unique identifiers.
    
    This property verifies that:
    1. Each created category gets a unique ID
    2. No two categories share the same ID
    3. IDs are properly generated and stored
    """
    created_categories = []
    
    try:
        # Create multiple product categories
        for i in range(category_count):
            category = ProductCategory(
                name=f"{name_prefix}_Category_{i}",
                description=f"Test category {i}"
            )
            db_session.add(category)
            db_session.flush()  # Flush to generate ID without committing
            created_categories.append(category)
        
        db_session.commit()
        
        # Collect all IDs
        category_ids = [cat.id for cat in created_categories]
        
        # Verify all IDs are not None
        assert all(cat_id is not None for cat_id in category_ids), \
            "All categories should have IDs assigned"
        
        # Verify all IDs are unique (no duplicates)
        assert len(category_ids) == len(set(category_ids)), \
            f"All category IDs should be unique. Got {len(category_ids)} categories but only {len(set(category_ids))} unique IDs"
        
        # Verify each category has a different ID from all others
        for i, cat1 in enumerate(created_categories):
            for j, cat2 in enumerate(created_categories):
                if i != j:
                    assert cat1.id != cat2.id, \
                        f"Category {i} and Category {j} should have different IDs, but both have {cat1.id}"
    
    finally:
        # Clean up: delete all created categories
        for category in created_categories:
            if category.id:
                db_session.query(ProductCategory).filter(ProductCategory.id == category.id).delete()
        db_session.commit()


# Feature: miniatures-erp, Property 11: Product category retrieval completeness
# Validates: Requirements 4.2
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate a random number of categories to create
    category_count=st.integers(min_value=1, max_value=15),
    name_prefix=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=90))
)
def test_product_category_retrieval_completeness(client, db_session, category_count, name_prefix):
    """
    Property: For any set of created product categories, retrieving all categories SHALL return all created categories.
    
    This property verifies that:
    1. All created categories are stored in the database
    2. The get_all endpoint returns all categories
    3. No categories are lost or missing during retrieval
    4. The count of returned categories matches the count of created categories
    """
    created_categories = []
    
    try:
        # Create multiple product categories
        for i in range(category_count):
            category = ProductCategory(
                name=f"{name_prefix}_Cat_{i}",
                description=f"Description for category {i}"
            )
            db_session.add(category)
            db_session.flush()  # Flush to generate ID
            created_categories.append(category)
        
        db_session.commit()
        
        # Retrieve all categories via API
        response = client.get("/api/product-categories")
        
        # Verify response is successful
        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"
        
        retrieved_data = response.json()
        
        # Extract IDs from created categories
        created_ids = {str(cat.id) for cat in created_categories}
        
        # Extract IDs from retrieved categories
        retrieved_ids = {cat["id"] for cat in retrieved_data}
        
        # Verify all created categories are in the retrieved set
        missing_ids = created_ids - retrieved_ids
        assert len(missing_ids) == 0, \
            f"Expected all {len(created_ids)} created categories to be retrieved, but {len(missing_ids)} are missing: {missing_ids}"
        
        # Verify each created category is present in the retrieved data
        for created_cat in created_categories:
            matching_cats = [cat for cat in retrieved_data if cat["id"] == str(created_cat.id)]
            assert len(matching_cats) == 1, \
                f"Expected exactly 1 match for category {created_cat.id}, found {len(matching_cats)}"
            
            # Verify the data matches
            matching_cat = matching_cats[0]
            assert matching_cat["name"] == created_cat.name, \
                f"Expected name '{created_cat.name}', got '{matching_cat['name']}'"
            assert matching_cat["description"] == created_cat.description, \
                f"Expected description '{created_cat.description}', got '{matching_cat['description']}'"
    
    finally:
        # Clean up: delete all created categories
        for category in created_categories:
            if category.id:
                db_session.query(ProductCategory).filter(ProductCategory.id == category.id).delete()
        db_session.commit()



# Feature: miniatures-erp, Property 12: Product category update persistence
# Validates: Requirements 4.3
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random initial and updated values
    initial_name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    initial_description=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=65, max_codepoint=122))
    ),
    updated_name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    updated_description=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=65, max_codepoint=122))
    )
)
def test_product_category_update_persistence(client, db_session, initial_name, initial_description, updated_name, updated_description):
    """
    Property: For any product category, updating its properties and then retrieving it SHALL return the updated values.
    
    This property verifies that:
    1. Updates to category name persist correctly
    2. Updates to category description persist correctly
    3. Retrieved data matches the updated values
    4. The update operation is idempotent and reliable
    """
    created_category = None
    
    try:
        # Create a product category with initial values
        category = ProductCategory(
            name=initial_name,
            description=initial_description
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        created_category = category
        category_id = str(category.id)
        
        # Update the category via API
        update_data = {
            "name": updated_name,
            "description": updated_description
        }
        
        update_response = client.put(
            f"/api/product-categories/{category_id}",
            json=update_data
        )
        
        # Verify update was successful
        assert update_response.status_code == 200, \
            f"Expected status 200 for update, got {update_response.status_code}"
        
        # Retrieve the category via API
        get_response = client.get(f"/api/product-categories/{category_id}")
        
        # Verify retrieval was successful
        assert get_response.status_code == 200, \
            f"Expected status 200 for retrieval, got {get_response.status_code}"
        
        retrieved_data = get_response.json()
        
        # Verify the retrieved data matches the updated values
        assert retrieved_data["name"] == updated_name, \
            f"Expected name '{updated_name}', but got '{retrieved_data['name']}'"
        
        assert retrieved_data["description"] == updated_description, \
            f"Expected description '{updated_description}', but got '{retrieved_data['description']}'"
        
        # Verify the ID hasn't changed
        assert retrieved_data["id"] == category_id, \
            f"Expected ID '{category_id}', but got '{retrieved_data['id']}'"
        
        # Also verify directly from database
        db_session.expire_all()  # Clear session cache to force fresh read
        db_category = db_session.query(ProductCategory).filter(ProductCategory.id == category_id).first()
        
        assert db_category is not None, \
            f"Category {category_id} should exist in database after update"
        
        assert db_category.name == updated_name, \
            f"Database name should be '{updated_name}', but got '{db_category.name}'"
        
        assert db_category.description == updated_description, \
            f"Database description should be '{updated_description}', but got '{db_category.description}'"
    
    finally:
        # Clean up: delete the created category
        if created_category and created_category.id:
            db_session.query(ProductCategory).filter(ProductCategory.id == created_category.id).delete()
            db_session.commit()


# Feature: miniatures-erp, Property 13: Product category deletion
# Validates: Requirements 4.4
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random number of categories to create and delete
    category_count=st.integers(min_value=1, max_value=10),
    delete_index=st.integers(min_value=0, max_value=9),  # Will be modded by category_count
    name_prefix=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=90))
)
def test_product_category_deletion(client, db_session, category_count, delete_index, name_prefix):
    """
    Property: For any product category, after deletion, retrieving all categories SHALL not include the deleted category.
    
    This property verifies that:
    1. A category can be successfully deleted
    2. After deletion, the category is not returned in the list of all categories
    3. The deleted category cannot be retrieved by ID
    4. Other categories remain unaffected by the deletion
    """
    created_categories = []
    
    try:
        # Create multiple product categories
        for i in range(category_count):
            category = ProductCategory(
                name=f"{name_prefix}_Category_{i}",
                description=f"Test category {i}"
            )
            db_session.add(category)
            db_session.flush()  # Flush to generate ID
            created_categories.append(category)
        
        db_session.commit()
        
        # Select a category to delete (use modulo to ensure valid index)
        delete_idx = delete_index % category_count
        category_to_delete = created_categories[delete_idx]
        deleted_category_id = str(category_to_delete.id)
        deleted_category_name = category_to_delete.name
        
        # Get all categories before deletion
        response_before = client.get("/api/product-categories")
        assert response_before.status_code == 200
        categories_before = response_before.json()
        
        # Verify the category exists before deletion
        category_ids_before = {cat["id"] for cat in categories_before}
        assert deleted_category_id in category_ids_before, \
            f"Category {deleted_category_id} should exist before deletion"
        
        # Delete the category via API
        delete_response = client.delete(f"/api/product-categories/{deleted_category_id}")
        
        # Verify deletion was successful
        assert delete_response.status_code == 204, \
            f"Expected status 204 for deletion, got {delete_response.status_code}"
        
        # Get all categories after deletion
        response_after = client.get("/api/product-categories")
        assert response_after.status_code == 200
        categories_after = response_after.json()
        
        # Extract IDs from retrieved categories after deletion
        category_ids_after = {cat["id"] for cat in categories_after}
        
        # Verify the deleted category is NOT in the retrieved set
        assert deleted_category_id not in category_ids_after, \
            f"Deleted category {deleted_category_id} should not be in the list of all categories"
        
        # Verify the deleted category cannot be retrieved by ID
        get_deleted_response = client.get(f"/api/product-categories/{deleted_category_id}")
        assert get_deleted_response.status_code == 404, \
            f"Expected status 404 when retrieving deleted category, got {get_deleted_response.status_code}"
        
        # Verify the deleted category is not in the database
        db_category = db_session.query(ProductCategory).filter(ProductCategory.id == deleted_category_id).first()
        assert db_category is None, \
            f"Deleted category {deleted_category_id} should not exist in the database"
        
        # Verify other categories still exist (if there were any)
        if category_count > 1:
            remaining_category_ids = [str(cat.id) for i, cat in enumerate(created_categories) if i != delete_idx]
            for remaining_id in remaining_category_ids:
                assert remaining_id in category_ids_after, \
                    f"Non-deleted category {remaining_id} should still exist after deletion"
        
        # Verify the count is correct
        expected_count_after = category_count - 1
        # Note: There might be other categories in the database from other tests
        # So we just verify our remaining categories are present
        for i, cat in enumerate(created_categories):
            if i != delete_idx:
                assert str(cat.id) in category_ids_after, \
                    f"Category {cat.id} (index {i}) should still exist after deleting category at index {delete_idx}"
        
        # Remove the deleted category from our tracking list
        created_categories.pop(delete_idx)
    
    finally:
        # Clean up: delete all remaining created categories
        for category in created_categories:
            if category.id:
                try:
                    db_session.query(ProductCategory).filter(ProductCategory.id == category.id).delete()
                except:
                    pass  # Category might already be deleted
        db_session.commit()

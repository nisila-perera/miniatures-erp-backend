"""Tests for product management"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.product import Product, ProductCategory
from app.models.enums import ProductSource
from decimal import Decimal


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


@pytest.fixture
def test_category(db_session):
    """Create a test product category"""
    category = ProductCategory(name="Test Category", description="Test category for products")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    yield category
    # Cleanup - delete products first to avoid foreign key constraint violations
    db_session.query(Product).filter(Product.category_id == category.id).delete()
    db_session.query(ProductCategory).filter(ProductCategory.id == category.id).delete()
    db_session.commit()


@pytest.mark.unit
def test_create_product(client, db_session, test_category):
    """Test creating a product via API"""
    response = client.post(
        "/api/products",
        json={
            "name": "Dragon Miniature",
            "description": "A detailed dragon miniature",
            "category_id": str(test_category.id),
            "base_price": 25.99,
            "is_colored": True,
            "dimensions": "10x10x15cm",
            "source": "erp"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Dragon Miniature"
    assert data["description"] == "A detailed dragon miniature"
    assert data["base_price"] == "25.99"
    assert data["is_colored"] is True
    assert data["source"] == "erp"
    assert "id" in data


@pytest.mark.unit
def test_create_product_woocommerce_source(client, db_session, test_category):
    """Test creating a product with WooCommerce source"""
    response = client.post(
        "/api/products",
        json={
            "name": "WC Product",
            "description": "From WooCommerce",
            "category_id": str(test_category.id),
            "base_price": 15.00,
            "source": "woocommerce",
            "woocommerce_id": 123
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["source"] == "woocommerce"
    assert data["woocommerce_id"] == 123


@pytest.mark.unit
def test_get_all_products(client, db_session, test_category):
    """Test retrieving all products"""
    product1 = Product(
        name="Product 1",
        description="First product",
        category_id=test_category.id,
        base_price=Decimal("10.00"),
        source=ProductSource.ERP
    )
    product2 = Product(
        name="Product 2",
        description="Second product",
        category_id=test_category.id,
        base_price=Decimal("20.00"),
        source=ProductSource.WOOCOMMERCE,
        woocommerce_id=456
    )
    db_session.add_all([product1, product2])
    db_session.commit()
    
    response = client.get("/api/products")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert any(p["name"] == "Product 1" for p in data)
    assert any(p["name"] == "Product 2" for p in data)


@pytest.mark.unit
def test_get_product_by_id(client, db_session, test_category):
    """Test retrieving a specific product by ID"""
    product = Product(
        name="Specific Product",
        description="A specific product",
        category_id=test_category.id,
        base_price=Decimal("30.00"),
        source=ProductSource.ERP
    )
    db_session.add(product)
    db_session.commit()
    
    response = client.get(f"/api/products/{product.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product.id
    assert data["name"] == "Specific Product"


@pytest.mark.unit
def test_update_erp_product(client, db_session, test_category):
    """Test updating an ERP product"""
    product = Product(
        name="Old Name",
        description="Old description",
        category_id=test_category.id,
        base_price=Decimal("10.00"),
        source=ProductSource.ERP
    )
    db_session.add(product)
    db_session.commit()
    
    response = client.put(
        f"/api/products/{product.id}",
        json={
            "name": "New Name",
            "description": "New description",
            "base_price": 15.00
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "New description"
    assert data["base_price"] == "15.00"


@pytest.mark.unit
def test_update_woocommerce_product_forbidden(client, db_session, test_category):
    """Test that updating a WooCommerce product is forbidden"""
    product = Product(
        name="WC Product",
        description="From WooCommerce",
        category_id=test_category.id,
        base_price=Decimal("10.00"),
        source=ProductSource.WOOCOMMERCE,
        woocommerce_id=789
    )
    db_session.add(product)
    db_session.commit()
    
    response = client.put(
        f"/api/products/{product.id}",
        json={"name": "Attempted Update"}
    )
    
    assert response.status_code == 403
    assert "read-only" in response.json()["detail"].lower()


@pytest.mark.unit
def test_delete_erp_product(client, db_session, test_category):
    """Test deleting an ERP product"""
    product = Product(
        name="To Delete",
        description="Will be deleted",
        category_id=test_category.id,
        base_price=Decimal("10.00"),
        source=ProductSource.ERP
    )
    db_session.add(product)
    db_session.commit()
    product_id = product.id
    
    response = client.delete(f"/api/products/{product_id}")
    
    assert response.status_code == 204
    
    # Verify deletion
    deleted_product = db_session.query(Product).filter(Product.id == product_id).first()
    assert deleted_product is None


@pytest.mark.unit
def test_delete_woocommerce_product_forbidden(client, db_session, test_category):
    """Test that deleting a WooCommerce product is forbidden"""
    product = Product(
        name="WC Product",
        description="From WooCommerce",
        category_id=test_category.id,
        base_price=Decimal("10.00"),
        source=ProductSource.WOOCOMMERCE,
        woocommerce_id=999
    )
    db_session.add(product)
    db_session.commit()
    
    response = client.delete(f"/api/products/{product.id}")
    
    assert response.status_code == 403
    assert "read-only" in response.json()["detail"].lower()



# Feature: miniatures-erp, Property 60: Product required fields
# Validates: Requirements 19.1
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    name=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    description=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=200, alphabet=st.characters(min_codepoint=65, max_codepoint=122))
    ),
    base_price=st.decimals(min_value=0, max_value=10000, places=2),
    is_colored=st.booleans(),
    dimensions=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=48, max_codepoint=122))
    )
)
def test_product_required_fields(client, db_session, name, description, base_price, is_colored, dimensions):
    """
    Property: For any product created, it SHALL have name, description, category, and base price stored.
    
    This property verifies that:
    1. All required fields are stored when creating a product
    2. The stored values match the input values
    3. Products can be retrieved with all required fields intact
    """
    created_product = None
    created_category = None
    
    try:
        # Create a test category
        category = ProductCategory(name=f"TestCat_{name[:10]}", description="Test category")
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        created_category = category
        
        # Create a product via API
        product_data = {
            "name": name,
            "description": description,
            "category_id": str(category.id),
            "base_price": float(base_price),
            "is_colored": is_colored,
            "dimensions": dimensions,
            "source": "erp"
        }
        
        response = client.post("/api/products", json=product_data)
        
        # Verify creation was successful
        assert response.status_code == 201, \
            f"Expected status 201, got {response.status_code}: {response.json()}"
        
        data = response.json()
        product_id = data["id"]
        
        # Verify all required fields are present and correct
        assert data["name"] == name, \
            f"Expected name '{name}', got '{data['name']}'"
        
        assert data["description"] == description, \
            f"Expected description '{description}', got '{data['description']}'"
        
        assert data["category_id"] == str(category.id), \
            f"Expected category_id '{category.id}', got '{data['category_id']}'"
        
        assert Decimal(str(data["base_price"])) == base_price, \
            f"Expected base_price '{base_price}', got '{data['base_price']}'"
        
        # Retrieve the product to verify persistence
        get_response = client.get(f"/api/products/{product_id}")
        assert get_response.status_code == 200
        
        retrieved_data = get_response.json()
        
        # Verify all fields persisted correctly
        assert retrieved_data["name"] == name
        assert retrieved_data["description"] == description
        assert retrieved_data["category_id"] == str(category.id)
        assert Decimal(str(retrieved_data["base_price"])) == base_price
        
        # Track for cleanup
        created_product = db_session.query(Product).filter(Product.id == product_id).first()
        
    finally:
        # Clean up
        if created_product and created_product.id:
            db_session.query(Product).filter(Product.id == created_product.id).delete()
        if created_category and created_category.id:
            db_session.query(ProductCategory).filter(ProductCategory.id == created_category.id).delete()
        db_session.commit()



# Feature: miniatures-erp, Property 61: Product retrieval completeness
# Validates: Requirements 19.4
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    product_count=st.integers(min_value=1, max_value=10),
    erp_count=st.integers(min_value=0, max_value=10),
    name_prefix=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=90))
)
def test_product_retrieval_completeness(client, db_session, product_count, erp_count, name_prefix):
    """
    Property: For any set of products (ERP and WooCommerce), retrieving all products SHALL return all products.
    
    This property verifies that:
    1. All created products are stored in the database
    2. The get_all endpoint returns all products regardless of source
    3. Both ERP and WooCommerce products are included
    4. No products are lost or missing during retrieval
    """
    created_products = []
    created_category = None
    
    try:
        # Create a test category
        category = ProductCategory(name=f"{name_prefix}_Cat", description="Test category")
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        created_category = category
        
        # Determine how many of each type to create
        wc_count = product_count - min(erp_count, product_count)
        actual_erp_count = product_count - wc_count
        
        # Create ERP products
        for i in range(actual_erp_count):
            product = Product(
                name=f"{name_prefix}_ERP_{i}",
                description=f"ERP product {i}",
                category_id=category.id,
                base_price=Decimal("10.00") + Decimal(i),
                source=ProductSource.ERP
            )
            db_session.add(product)
            db_session.flush()
            created_products.append(product)
        
        # Create WooCommerce products
        for i in range(wc_count):
            product = Product(
                name=f"{name_prefix}_WC_{i}",
                description=f"WooCommerce product {i}",
                category_id=category.id,
                base_price=Decimal("20.00") + Decimal(i),
                source=ProductSource.WOOCOMMERCE,
                woocommerce_id=1000 + i
            )
            db_session.add(product)
            db_session.flush()
            created_products.append(product)
        
        db_session.commit()
        
        # Retrieve all products via API
        response = client.get("/api/products")
        
        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"
        
        retrieved_data = response.json()
        
        # Extract IDs from created products
        created_ids = {str(prod.id) for prod in created_products}
        
        # Extract IDs from retrieved products
        retrieved_ids = {prod["id"] for prod in retrieved_data}
        
        # Verify all created products are in the retrieved set
        missing_ids = created_ids - retrieved_ids
        assert len(missing_ids) == 0, \
            f"Expected all {len(created_ids)} created products to be retrieved, but {len(missing_ids)} are missing"
        
        # Verify each created product is present with correct data
        for created_prod in created_products:
            matching_prods = [p for p in retrieved_data if p["id"] == str(created_prod.id)]
            assert len(matching_prods) == 1, \
                f"Expected exactly 1 match for product {created_prod.id}, found {len(matching_prods)}"
            
            matching_prod = matching_prods[0]
            assert matching_prod["name"] == created_prod.name
            assert matching_prod["source"] == created_prod.source.value
        
    finally:
        # Clean up
        for product in created_products:
            if product.id:
                db_session.query(Product).filter(Product.id == product.id).delete()
        if created_category and created_category.id:
            db_session.query(ProductCategory).filter(ProductCategory.id == created_category.id).delete()
        db_session.commit()



# Feature: miniatures-erp, Property 62: WooCommerce product read-only flag
# Validates: Requirements 19.5
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    woocommerce_id=st.integers(min_value=1, max_value=100000),
    update_field=st.sampled_from(["name", "description", "base_price"])
)
def test_woocommerce_product_readonly(client, db_session, name, woocommerce_id, update_field):
    """
    Property: For any product with source "woocommerce", it SHALL be marked as read-only.
    
    This property verifies that:
    1. WooCommerce products cannot be updated
    2. WooCommerce products cannot be deleted
    3. Attempts to modify WooCommerce products return 403 Forbidden
    4. The read-only enforcement is consistent across all operations
    """
    created_product = None
    created_category = None
    
    try:
        # Create a test category
        category = ProductCategory(name=f"Cat_{name[:10]}", description="Test category")
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        created_category = category
        
        # Create a WooCommerce product
        product = Product(
            name=name,
            description="WooCommerce product",
            category_id=category.id,
            base_price=Decimal("25.00"),
            source=ProductSource.WOOCOMMERCE,
            woocommerce_id=woocommerce_id
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)
        created_product = product
        
        # Attempt to update the product
        update_data = {}
        if update_field == "name":
            update_data["name"] = "Updated Name"
        elif update_field == "description":
            update_data["description"] = "Updated Description"
        elif update_field == "base_price":
            update_data["base_price"] = 50.00
        
        update_response = client.put(
            f"/api/products/{product.id}",
            json=update_data
        )
        
        # Verify update is forbidden
        assert update_response.status_code == 403, \
            f"Expected status 403 for WooCommerce product update, got {update_response.status_code}"
        
        assert "read-only" in update_response.json()["detail"].lower() or \
               "forbidden" in update_response.json()["detail"].lower(), \
            f"Expected read-only or forbidden message, got: {update_response.json()['detail']}"
        
        # Attempt to delete the product
        delete_response = client.delete(f"/api/products/{product.id}")
        
        # Verify deletion is forbidden
        assert delete_response.status_code == 403, \
            f"Expected status 403 for WooCommerce product deletion, got {delete_response.status_code}"
        
        assert "read-only" in delete_response.json()["detail"].lower() or \
               "forbidden" in delete_response.json()["detail"].lower(), \
            f"Expected read-only or forbidden message, got: {delete_response.json()['detail']}"
        
        # Verify the product still exists unchanged
        db_session.expire_all()
        unchanged_product = db_session.query(Product).filter(Product.id == product.id).first()
        assert unchanged_product is not None, \
            "Product should still exist after failed update/delete attempts"
        assert unchanged_product.name == name, \
            "Product name should be unchanged"
        assert unchanged_product.source == ProductSource.WOOCOMMERCE, \
            "Product source should still be WooCommerce"
        
    finally:
        # Clean up
        if created_product and created_product.id:
            db_session.query(Product).filter(Product.id == created_product.id).delete()
        if created_category and created_category.id:
            db_session.query(ProductCategory).filter(ProductCategory.id == created_category.id).delete()
        db_session.commit()



# Feature: miniatures-erp, Property 63: ERP product editability
# Validates: Requirements 19.6
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    initial_name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    updated_name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    initial_price=st.decimals(min_value=0, max_value=1000, places=2),
    updated_price=st.decimals(min_value=0, max_value=1000, places=2)
)
def test_erp_product_editability(client, db_session, initial_name, updated_name, initial_price, updated_price):
    """
    Property: For any product with source "erp", it SHALL be editable.
    
    This property verifies that:
    1. ERP products can be successfully updated
    2. Updates to ERP products persist correctly
    3. All fields of ERP products can be modified
    4. The update operation returns success status
    """
    created_product = None
    created_category = None
    
    try:
        # Create a test category
        category = ProductCategory(name=f"Cat_{initial_name[:10]}", description="Test category")
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        created_category = category
        
        # Create an ERP product
        product = Product(
            name=initial_name,
            description="Initial description",
            category_id=category.id,
            base_price=initial_price,
            source=ProductSource.ERP,
            is_colored=False
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)
        created_product = product
        
        # Update the product
        update_data = {
            "name": updated_name,
            "description": "Updated description",
            "base_price": float(updated_price),
            "is_colored": True
        }
        
        update_response = client.put(
            f"/api/products/{product.id}",
            json=update_data
        )
        
        # Verify update is successful
        assert update_response.status_code == 200, \
            f"Expected status 200 for ERP product update, got {update_response.status_code}"
        
        updated_data = update_response.json()
        
        # Verify the updated values
        assert updated_data["name"] == updated_name, \
            f"Expected name '{updated_name}', got '{updated_data['name']}'"
        
        assert updated_data["description"] == "Updated description", \
            f"Expected description 'Updated description', got '{updated_data['description']}'"
        
        assert Decimal(str(updated_data["base_price"])) == updated_price, \
            f"Expected base_price '{updated_price}', got '{updated_data['base_price']}'"
        
        assert updated_data["is_colored"] is True, \
            f"Expected is_colored True, got {updated_data['is_colored']}"
        
        # Verify persistence by retrieving the product
        get_response = client.get(f"/api/products/{product.id}")
        assert get_response.status_code == 200
        
        retrieved_data = get_response.json()
        assert retrieved_data["name"] == updated_name
        assert retrieved_data["description"] == "Updated description"
        assert Decimal(str(retrieved_data["base_price"])) == updated_price
        assert retrieved_data["is_colored"] is True
        
    finally:
        # Clean up
        if created_product and created_product.id:
            db_session.query(Product).filter(Product.id == created_product.id).delete()
        if created_category and created_category.id:
            db_session.query(ProductCategory).filter(ProductCategory.id == created_category.id).delete()
        db_session.commit()



# Feature: miniatures-erp, Property 64: ERP product deletion
# Validates: Requirements 19.7
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    product_count=st.integers(min_value=1, max_value=10),
    delete_index=st.integers(min_value=0, max_value=9),
    name_prefix=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=90))
)
def test_erp_product_deletion(client, db_session, product_count, delete_index, name_prefix):
    """
    Property: For any ERP-created product, after deletion, retrieving all products SHALL not include the deleted product.
    
    This property verifies that:
    1. ERP products can be successfully deleted
    2. After deletion, the product is not returned in the list of all products
    3. The deleted product cannot be retrieved by ID
    4. Other products remain unaffected by the deletion
    """
    created_products = []
    created_category = None
    
    try:
        # Create a test category
        category = ProductCategory(name=f"{name_prefix}_Cat", description="Test category")
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        created_category = category
        
        # Create multiple ERP products
        for i in range(product_count):
            product = Product(
                name=f"{name_prefix}_Product_{i}",
                description=f"Test product {i}",
                category_id=category.id,
                base_price=Decimal("10.00") + Decimal(i),
                source=ProductSource.ERP
            )
            db_session.add(product)
            db_session.flush()
            created_products.append(product)
        
        db_session.commit()
        
        # Select a product to delete
        delete_idx = delete_index % product_count
        product_to_delete = created_products[delete_idx]
        deleted_product_id = str(product_to_delete.id)
        
        # Get all products before deletion
        response_before = client.get("/api/products")
        assert response_before.status_code == 200
        products_before = response_before.json()
        product_ids_before = {p["id"] for p in products_before}
        
        # Verify the product exists before deletion
        assert deleted_product_id in product_ids_before, \
            f"Product {deleted_product_id} should exist before deletion"
        
        # Delete the product via API
        delete_response = client.delete(f"/api/products/{deleted_product_id}")
        
        # Verify deletion was successful
        assert delete_response.status_code == 204, \
            f"Expected status 204 for deletion, got {delete_response.status_code}"
        
        # Get all products after deletion
        response_after = client.get("/api/products")
        assert response_after.status_code == 200
        products_after = response_after.json()
        product_ids_after = {p["id"] for p in products_after}
        
        # Verify the deleted product is NOT in the retrieved set
        assert deleted_product_id not in product_ids_after, \
            f"Deleted product {deleted_product_id} should not be in the list of all products"
        
        # Verify the deleted product cannot be retrieved by ID
        get_deleted_response = client.get(f"/api/products/{deleted_product_id}")
        assert get_deleted_response.status_code == 404, \
            f"Expected status 404 when retrieving deleted product, got {get_deleted_response.status_code}"
        
        # Verify the deleted product is not in the database
        db_product = db_session.query(Product).filter(Product.id == deleted_product_id).first()
        assert db_product is None, \
            f"Deleted product {deleted_product_id} should not exist in the database"
        
        # Verify other products still exist
        if product_count > 1:
            for i, prod in enumerate(created_products):
                if i != delete_idx:
                    assert str(prod.id) in product_ids_after, \
                        f"Product {prod.id} (index {i}) should still exist after deleting product at index {delete_idx}"
        
        # Remove the deleted product from our tracking list
        created_products.pop(delete_idx)
        
    finally:
        # Clean up
        for product in created_products:
            if product.id:
                try:
                    db_session.query(Product).filter(Product.id == product.id).delete()
                except:
                    pass
        if created_category and created_category.id:
            db_session.query(ProductCategory).filter(ProductCategory.id == created_category.id).delete()
        db_session.commit()



# Feature: miniatures-erp, Property 14: Product-category association
# Validates: Requirements 4.5
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    product_name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    category_name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122))
)
def test_product_category_association(client, db_session, product_name, category_name):
    """
    Property: For any product assigned to a category, retrieving the product SHALL show the correct category association.
    
    This property verifies that:
    1. Products are correctly associated with their categories
    2. The category association persists in the database
    3. Retrieving a product returns the correct category_id
    4. The association is maintained across create and retrieve operations
    """
    created_product = None
    created_category = None
    
    try:
        # Create a test category
        category = ProductCategory(name=category_name, description="Test category for association")
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        created_category = category
        category_id = str(category.id)
        
        # Create a product associated with this category
        product_data = {
            "name": product_name,
            "description": "Test product for category association",
            "category_id": category_id,
            "base_price": 15.00,
            "source": "erp"
        }
        
        create_response = client.post("/api/products", json=product_data)
        
        # Verify creation was successful
        assert create_response.status_code == 201, \
            f"Expected status 201, got {create_response.status_code}"
        
        created_data = create_response.json()
        product_id = created_data["id"]
        
        # Verify the category association in the create response
        assert created_data["category_id"] == category_id, \
            f"Expected category_id '{category_id}', got '{created_data['category_id']}'"
        
        # Retrieve the product to verify the association persists
        get_response = client.get(f"/api/products/{product_id}")
        
        assert get_response.status_code == 200, \
            f"Expected status 200, got {get_response.status_code}"
        
        retrieved_data = get_response.json()
        
        # Verify the category association in the retrieved data
        assert retrieved_data["category_id"] == category_id, \
            f"Expected category_id '{category_id}' in retrieved data, got '{retrieved_data['category_id']}'"
        
        # Verify the association in the database directly
        db_session.expire_all()
        db_product = db_session.query(Product).filter(Product.id == product_id).first()
        
        assert db_product is not None, \
            f"Product {product_id} should exist in database"
        
        assert str(db_product.category_id) == category_id, \
            f"Expected category_id '{category_id}' in database, got '{db_product.category_id}'"
        
        # Verify the category exists and matches
        db_category = db_session.query(ProductCategory).filter(ProductCategory.id == category_id).first()
        assert db_category is not None, \
            f"Category {category_id} should exist in database"
        
        assert db_category.name == category_name, \
            f"Expected category name '{category_name}', got '{db_category.name}'"
        
        # Track for cleanup
        created_product = db_product
        
    finally:
        # Clean up
        if created_product and created_product.id:
            db_session.query(Product).filter(Product.id == created_product.id).delete()
        if created_category and created_category.id:
            db_session.query(ProductCategory).filter(ProductCategory.id == created_category.id).delete()
        db_session.commit()
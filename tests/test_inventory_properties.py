"""Property-based tests for inventory management"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from datetime import date, timedelta
from decimal import Decimal
from app.main import app
from app.core.database import get_db
from app.models.inventory import Resin, PaintBottle


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


# Feature: miniatures-erp, Property 33: Resin color recording
# Validates: Requirements 10.1
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    color=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    quantity=st.decimals(min_value=0.01, max_value=1000, places=2),
    cost_per_unit=st.decimals(min_value=0, max_value=10000, places=2),
    days_ago=st.integers(min_value=0, max_value=365)
)
def test_resin_color_recording(client, db_session, color, quantity, cost_per_unit, days_ago):
    """
    Property: For any resin added to inventory, it SHALL have a color recorded.
    
    This property verifies that:
    1. When a resin entry is created, the color is stored
    2. The color can be retrieved from the database
    3. The color value matches what was provided during creation
    """
    created_resin = None
    
    try:
        # Calculate purchase date
        purchase_date = date.today() - timedelta(days=days_ago)
        
        # Create a resin entry via API
        resin_data = {
            "color": color,
            "quantity": float(quantity),
            "unit": "kg",
            "cost_per_unit": float(cost_per_unit),
            "purchase_date": purchase_date.isoformat()
        }
        
        create_response = client.post("/api/inventory/resin", json=resin_data)
        
        # Verify creation was successful
        assert create_response.status_code == 201, \
            f"Expected status 201 for creation, got {create_response.status_code}"
        
        created_data = create_response.json()
        resin_id = created_data["id"]
        
        # Verify the color is present in the response
        assert "color" in created_data, \
            "Created resin should have a color field"
        
        assert created_data["color"] is not None, \
            "Created resin color should not be None"
        
        assert created_data["color"] == color, \
            f"Expected color '{color}', but got '{created_data['color']}'"
        
        # Retrieve the resin via API to verify persistence
        get_response = client.get(f"/api/inventory/resin/{resin_id}")
        
        assert get_response.status_code == 200, \
            f"Expected status 200 for retrieval, got {get_response.status_code}"
        
        retrieved_data = get_response.json()
        
        # Verify the color is recorded and matches
        assert "color" in retrieved_data, \
            "Retrieved resin should have a color field"
        
        assert retrieved_data["color"] is not None, \
            "Retrieved resin color should not be None"
        
        assert retrieved_data["color"] == color, \
            f"Expected retrieved color '{color}', but got '{retrieved_data['color']}'"
        
        # Verify directly from database
        db_resin = db_session.query(Resin).filter(Resin.id == resin_id).first()
        
        assert db_resin is not None, \
            f"Resin {resin_id} should exist in database"
        
        assert db_resin.color is not None, \
            "Database resin color should not be None"
        
        assert db_resin.color == color, \
            f"Database color should be '{color}', but got '{db_resin.color}'"
        
        created_resin = db_resin
    
    finally:
        # Clean up: delete the created resin
        if created_resin and created_resin.id:
            db_session.query(Resin).filter(Resin.id == created_resin.id).delete()
            db_session.commit()


# Feature: miniatures-erp, Property 34: Paint bottle required fields
# Validates: Requirements 10.2
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    color=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    brand=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    volume_ml=st.decimals(min_value=1, max_value=1000, places=2),
    cost=st.decimals(min_value=0, max_value=10000, places=2),
    days_ago=st.integers(min_value=0, max_value=365)
)
def test_paint_bottle_required_fields(client, db_session, color, brand, volume_ml, cost, days_ago):
    """
    Property: For any paint bottle added to inventory, it SHALL have volume, color, brand, and cost recorded.
    
    This property verifies that:
    1. When a paint bottle is created, all required fields are stored
    2. Volume (volume_ml), color, brand, and cost are all present
    3. All values can be retrieved and match what was provided
    """
    created_paint = None
    
    try:
        # Calculate purchase date
        purchase_date = date.today() - timedelta(days=days_ago)
        
        # Ensure current_volume_ml doesn't exceed volume_ml
        current_volume_ml = volume_ml
        
        # Create a paint bottle entry via API
        paint_data = {
            "color": color,
            "brand": brand,
            "volume_ml": float(volume_ml),
            "current_volume_ml": float(current_volume_ml),
            "cost": float(cost),
            "purchase_date": purchase_date.isoformat()
        }
        
        create_response = client.post("/api/inventory/paint", json=paint_data)
        
        # Verify creation was successful
        assert create_response.status_code == 201, \
            f"Expected status 201 for creation, got {create_response.status_code}"
        
        created_data = create_response.json()
        paint_id = created_data["id"]
        
        # Verify all required fields are present in the response
        assert "volume_ml" in created_data, \
            "Created paint bottle should have volume_ml field"
        assert "color" in created_data, \
            "Created paint bottle should have color field"
        assert "brand" in created_data, \
            "Created paint bottle should have brand field"
        assert "cost" in created_data, \
            "Created paint bottle should have cost field"
        
        # Verify none of the required fields are None
        assert created_data["volume_ml"] is not None, \
            "Paint bottle volume_ml should not be None"
        assert created_data["color"] is not None, \
            "Paint bottle color should not be None"
        assert created_data["brand"] is not None, \
            "Paint bottle brand should not be None"
        assert created_data["cost"] is not None, \
            "Paint bottle cost should not be None"
        
        # Verify the values match what was provided
        assert Decimal(str(created_data["volume_ml"])) == volume_ml, \
            f"Expected volume_ml '{volume_ml}', but got '{created_data['volume_ml']}'"
        assert created_data["color"] == color, \
            f"Expected color '{color}', but got '{created_data['color']}'"
        assert created_data["brand"] == brand, \
            f"Expected brand '{brand}', but got '{created_data['brand']}'"
        assert Decimal(str(created_data["cost"])) == cost, \
            f"Expected cost '{cost}', but got '{created_data['cost']}'"
        
        # Retrieve the paint bottle via API to verify persistence
        get_response = client.get(f"/api/inventory/paint/{paint_id}")
        
        assert get_response.status_code == 200, \
            f"Expected status 200 for retrieval, got {get_response.status_code}"
        
        retrieved_data = get_response.json()
        
        # Verify all required fields are present and match
        assert retrieved_data["volume_ml"] is not None and Decimal(str(retrieved_data["volume_ml"])) == volume_ml, \
            f"Retrieved volume_ml should be '{volume_ml}'"
        assert retrieved_data["color"] is not None and retrieved_data["color"] == color, \
            f"Retrieved color should be '{color}'"
        assert retrieved_data["brand"] is not None and retrieved_data["brand"] == brand, \
            f"Retrieved brand should be '{brand}'"
        assert retrieved_data["cost"] is not None and Decimal(str(retrieved_data["cost"])) == cost, \
            f"Retrieved cost should be '{cost}'"
        
        # Verify directly from database
        db_paint = db_session.query(PaintBottle).filter(PaintBottle.id == paint_id).first()
        
        assert db_paint is not None, \
            f"Paint bottle {paint_id} should exist in database"
        
        assert db_paint.volume_ml is not None and db_paint.volume_ml == volume_ml, \
            f"Database volume_ml should be '{volume_ml}'"
        assert db_paint.color is not None and db_paint.color == color, \
            f"Database color should be '{color}'"
        assert db_paint.brand is not None and db_paint.brand == brand, \
            f"Database brand should be '{brand}'"
        assert db_paint.cost is not None and db_paint.cost == cost, \
            f"Database cost should be '{cost}'"
        
        created_paint = db_paint
    
    finally:
        # Clean up: delete the created paint bottle
        if created_paint and created_paint.id:
            db_session.query(PaintBottle).filter(PaintBottle.id == created_paint.id).delete()
            db_session.commit()


# Feature: miniatures-erp, Property 35: Raw material purchase date recording
# Validates: Requirements 10.5
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Test both resin and paint bottles
    material_type=st.sampled_from(["resin", "paint"]),
    color=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    days_ago=st.integers(min_value=0, max_value=365)
)
def test_raw_material_purchase_date_recording(client, db_session, material_type, color, days_ago):
    """
    Property: For any raw material added to inventory, it SHALL have a purchase date recorded.
    
    This property verifies that:
    1. When a raw material (resin or paint) is created, the purchase date is stored
    2. The purchase date can be retrieved from the database
    3. The purchase date value matches what was provided during creation
    """
    created_material = None
    material_id = None
    
    try:
        # Calculate purchase date
        purchase_date = date.today() - timedelta(days=days_ago)
        
        if material_type == "resin":
            # Create a resin entry
            material_data = {
                "color": color,
                "quantity": 10.5,
                "unit": "kg",
                "cost_per_unit": 50.0,
                "purchase_date": purchase_date.isoformat()
            }
            
            create_response = client.post("/api/inventory/resin", json=material_data)
            endpoint_prefix = "/api/inventory/resin"
            model_class = Resin
        else:
            # Create a paint bottle entry
            material_data = {
                "color": color,
                "brand": "TestBrand",
                "volume_ml": 50.0,
                "current_volume_ml": 50.0,
                "cost": 15.0,
                "purchase_date": purchase_date.isoformat()
            }
            
            create_response = client.post("/api/inventory/paint", json=material_data)
            endpoint_prefix = "/api/inventory/paint"
            model_class = PaintBottle
        
        # Verify creation was successful
        assert create_response.status_code == 201, \
            f"Expected status 201 for {material_type} creation, got {create_response.status_code}"
        
        created_data = create_response.json()
        material_id = created_data["id"]
        
        # Verify the purchase date is present in the response
        assert "purchase_date" in created_data, \
            f"Created {material_type} should have a purchase_date field"
        
        assert created_data["purchase_date"] is not None, \
            f"Created {material_type} purchase_date should not be None"
        
        assert created_data["purchase_date"] == purchase_date.isoformat(), \
            f"Expected purchase_date '{purchase_date.isoformat()}', but got '{created_data['purchase_date']}'"
        
        # Retrieve the material via API to verify persistence
        get_response = client.get(f"{endpoint_prefix}/{material_id}")
        
        assert get_response.status_code == 200, \
            f"Expected status 200 for {material_type} retrieval, got {get_response.status_code}"
        
        retrieved_data = get_response.json()
        
        # Verify the purchase date is recorded and matches
        assert "purchase_date" in retrieved_data, \
            f"Retrieved {material_type} should have a purchase_date field"
        
        assert retrieved_data["purchase_date"] is not None, \
            f"Retrieved {material_type} purchase_date should not be None"
        
        assert retrieved_data["purchase_date"] == purchase_date.isoformat(), \
            f"Expected retrieved purchase_date '{purchase_date.isoformat()}', but got '{retrieved_data['purchase_date']}'"
        
        # Verify directly from database
        db_material = db_session.query(model_class).filter(model_class.id == material_id).first()
        
        assert db_material is not None, \
            f"{material_type.capitalize()} {material_id} should exist in database"
        
        assert db_material.purchase_date is not None, \
            f"Database {material_type} purchase_date should not be None"
        
        assert db_material.purchase_date == purchase_date, \
            f"Database purchase_date should be '{purchase_date}', but got '{db_material.purchase_date}'"
        
        created_material = db_material
    
    finally:
        # Clean up: delete the created material
        if created_material and material_id:
            if material_type == "resin":
                db_session.query(Resin).filter(Resin.id == material_id).delete()
            else:
                db_session.query(PaintBottle).filter(PaintBottle.id == material_id).delete()
            db_session.commit()


# Feature: miniatures-erp, Property 36: Raw material update persistence
# Validates: Requirements 10.7
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Test both resin and paint bottles
    material_type=st.sampled_from(["resin", "paint"]),
    color=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    initial_quantity=st.decimals(min_value=1, max_value=100, places=2),
    updated_quantity=st.decimals(min_value=1, max_value=100, places=2)
)
def test_raw_material_update_persistence(client, db_session, material_type, color, initial_quantity, updated_quantity):
    """
    Property: For any raw material, updating its quantity and then retrieving it SHALL return the updated quantity.
    
    This property verifies that:
    1. Updates to raw material quantities persist correctly
    2. Retrieved data matches the updated values
    3. The update operation is reliable for both resin and paint bottles
    """
    created_material = None
    material_id = None
    
    try:
        # Create initial material with initial quantity
        if material_type == "resin":
            initial_data = {
                "color": color,
                "quantity": float(initial_quantity),
                "unit": "kg",
                "cost_per_unit": 50.0,
                "purchase_date": date.today().isoformat()
            }
            
            create_response = client.post("/api/inventory/resin", json=initial_data)
            endpoint_prefix = "/api/inventory/resin"
            model_class = Resin
            quantity_field = "quantity"
        else:
            # For paint bottles, we update current_volume_ml
            initial_data = {
                "color": color,
                "brand": "TestBrand",
                "volume_ml": 100.0,
                "current_volume_ml": float(initial_quantity),
                "cost": 15.0,
                "purchase_date": date.today().isoformat()
            }
            
            create_response = client.post("/api/inventory/paint", json=initial_data)
            endpoint_prefix = "/api/inventory/paint"
            model_class = PaintBottle
            quantity_field = "current_volume_ml"
        
        # Verify creation was successful
        assert create_response.status_code == 201, \
            f"Expected status 201 for {material_type} creation, got {create_response.status_code}"
        
        created_data = create_response.json()
        material_id = created_data["id"]
        
        # Verify initial quantity is correct
        assert quantity_field in created_data, \
            f"Created {material_type} should have {quantity_field} field"
        
        assert Decimal(str(created_data[quantity_field])) == initial_quantity, \
            f"Initial {quantity_field} should be '{initial_quantity}', but got '{created_data[quantity_field]}'"
        
        # Update the quantity
        update_data = {
            quantity_field: float(updated_quantity)
        }
        
        update_response = client.put(f"{endpoint_prefix}/{material_id}", json=update_data)
        
        assert update_response.status_code == 200, \
            f"Expected status 200 for {material_type} update, got {update_response.status_code}"
        
        # Retrieve the material via API to verify persistence
        get_response = client.get(f"{endpoint_prefix}/{material_id}")
        
        assert get_response.status_code == 200, \
            f"Expected status 200 for {material_type} retrieval, got {get_response.status_code}"
        
        retrieved_data = get_response.json()
        
        # Verify the updated quantity persisted
        assert quantity_field in retrieved_data, \
            f"Retrieved {material_type} should have {quantity_field} field"
        
        assert Decimal(str(retrieved_data[quantity_field])) == updated_quantity, \
            f"Updated {quantity_field} should be '{updated_quantity}', but got '{retrieved_data[quantity_field]}'"
        
        # Verify directly from database
        db_material = db_session.query(model_class).filter(model_class.id == material_id).first()
        
        assert db_material is not None, \
            f"{material_type.capitalize()} {material_id} should exist in database"
        
        db_quantity = getattr(db_material, quantity_field)
        
        assert db_quantity is not None, \
            f"Database {material_type} {quantity_field} should not be None"
        
        assert db_quantity == updated_quantity, \
            f"Database {quantity_field} should be '{updated_quantity}', but got '{db_quantity}'"
        
        created_material = db_material
    
    finally:
        # Clean up: delete the created material
        if created_material and material_id:
            if material_type == "resin":
                db_session.query(Resin).filter(Resin.id == material_id).delete()
            else:
                db_session.query(PaintBottle).filter(PaintBottle.id == material_id).delete()
            db_session.commit()

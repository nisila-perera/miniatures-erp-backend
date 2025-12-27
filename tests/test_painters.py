"""Tests for painter management"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.painter import Painter


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


def test_create_painter(client, db_session):
    """Test creating a painter"""
    painter_data = {
        "name": "John Smith",
        "email": "john@example.com",
        "phone": "555-1234",
        "is_active": True
    }
    
    response = client.post("/api/painters", json=painter_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Smith"
    assert data["email"] == "john@example.com"
    assert data["phone"] == "555-1234"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_painter(client, db_session):
    """Test retrieving a painter"""
    # Create a painter first
    painter_data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "555-5678",
        "is_active": True
    }
    
    create_response = client.post("/api/painters", json=painter_data)
    painter_id = create_response.json()["id"]
    
    # Retrieve the painter
    response = client.get(f"/api/painters/{painter_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == painter_id
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane@example.com"


def test_get_all_painters(client, db_session):
    """Test retrieving all painters"""
    # Create multiple painters
    painters = [
        {"name": "Painter 1", "email": "painter1@example.com", "phone": "555-0001"},
        {"name": "Painter 2", "email": "painter2@example.com", "phone": "555-0002"},
        {"name": "Painter 3", "email": "painter3@example.com", "phone": "555-0003"}
    ]
    
    for painter_data in painters:
        client.post("/api/painters", json=painter_data)
    
    # Get all painters
    response = client.get("/api/painters")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    
    # Verify all created painters are in the list
    names = [p["name"] for p in data]
    assert "Painter 1" in names
    assert "Painter 2" in names
    assert "Painter 3" in names


def test_update_painter(client, db_session):
    """Test updating a painter"""
    # Create a painter
    painter_data = {
        "name": "Original Name",
        "email": "original@example.com",
        "phone": "555-0000",
        "is_active": True
    }
    
    create_response = client.post("/api/painters", json=painter_data)
    painter_id = create_response.json()["id"]
    
    # Update the painter
    update_data = {
        "name": "Updated Name",
        "email": "updated@example.com",
        "is_active": False
    }
    
    response = client.put(f"/api/painters/{painter_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["email"] == "updated@example.com"
    assert data["is_active"] is False
    assert data["phone"] == "555-0000"  # Unchanged field should persist


def test_delete_painter(client, db_session):
    """Test deleting a painter"""
    # Create a painter
    painter_data = {
        "name": "To Delete",
        "email": "delete@example.com",
        "phone": "555-9999"
    }
    
    create_response = client.post("/api/painters", json=painter_data)
    painter_id = create_response.json()["id"]
    
    # Delete the painter
    response = client.delete(f"/api/painters/{painter_id}")
    
    assert response.status_code == 204
    
    # Verify the painter is deleted
    get_response = client.get(f"/api/painters/{painter_id}")
    assert get_response.status_code == 404


def test_create_painter_without_name_fails(client):
    """Test that creating a painter without a name fails"""
    painter_data = {
        "name": "",
        "email": "test@example.com"
    }
    
    response = client.post("/api/painters", json=painter_data)
    
    assert response.status_code == 400
    assert "name cannot be empty" in response.json()["detail"].lower()


def test_get_nonexistent_painter(client):
    """Test retrieving a nonexistent painter"""
    # Use a valid UUID format that doesn't exist
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/painters/{fake_uuid}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_nonexistent_painter(client):
    """Test updating a nonexistent painter"""
    # Use a valid UUID format that doesn't exist
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    update_data = {"name": "Updated"}
    
    response = client.put(f"/api/painters/{fake_uuid}", json=update_data)
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_nonexistent_painter(client):
    """Test deleting a nonexistent painter"""
    # Use a valid UUID format that doesn't exist
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/api/painters/{fake_uuid}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_painter_with_optional_fields(client):
    """Test creating a painter with optional fields"""
    painter_data = {
        "name": "Full Details Painter",
        "email": "full@example.com",
        "phone": "555-1111",
        "is_active": True
    }
    
    response = client.post("/api/painters", json=painter_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "full@example.com"
    assert data["phone"] == "555-1111"
    assert data["is_active"] is True


def test_create_painter_with_minimal_fields(client):
    """Test creating a painter with only required fields"""
    painter_data = {
        "name": "Minimal Painter"
    }
    
    response = client.post("/api/painters", json=painter_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal Painter"
    assert data["email"] is None
    assert data["phone"] is None
    assert data["is_active"] is True  # Default value

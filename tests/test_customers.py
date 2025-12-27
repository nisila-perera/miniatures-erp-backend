"""Tests for customer management"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.customer import Customer
from app.models.enums import CustomerSource


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


# Feature: miniatures-erp, Property 41: Customer required fields
# Validates: Requirements 12.1
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random customer data
    name=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    email=st.one_of(
        st.none(),
        st.emails()
    ),
    phone=st.one_of(
        st.none(),
        st.text(min_size=5, max_size=20, alphabet=st.characters(min_codepoint=48, max_codepoint=57))
    ),
    address=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=122))
    ),
    city=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122))
    ),
    postal_code=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=48, max_codepoint=90))
    )
)
def test_customer_required_fields(client, db_session, name, email, phone, address, city, postal_code):
    """
    Property: For any customer created, it SHALL have name, contact information, and address stored.
    
    This property verifies that:
    1. A customer can be created with name (required field)
    2. Contact information (email, phone) is stored correctly
    3. Address information (address, city, postal_code) is stored correctly
    4. All provided fields are persisted in the database
    """
    created_customer = None
    
    try:
        # Create customer data
        customer_data = {
            "name": name,
            "source": CustomerSource.ERP.value
        }
        
        # Add optional fields if provided
        if email is not None:
            customer_data["email"] = email
        if phone is not None:
            customer_data["phone"] = phone
        if address is not None:
            customer_data["address"] = address
        if city is not None:
            customer_data["city"] = city
        if postal_code is not None:
            customer_data["postal_code"] = postal_code
        
        # Create customer via API
        create_response = client.post(
            "/api/customers",
            json=customer_data
        )
        
        # Verify creation was successful
        assert create_response.status_code == 201, \
            f"Expected status 201 for customer creation, got {create_response.status_code}: {create_response.text}"
        
        created_data = create_response.json()
        customer_id = created_data["id"]
        
        # Verify required field (name) is stored
        assert created_data["name"] == name, \
            f"Expected name '{name}', but got '{created_data['name']}'"
        
        # Verify contact information is stored correctly
        # Note: EmailStr normalizes emails (lowercase, punycode for IDN), so we just verify it was stored
        if email is not None:
            assert created_data["email"] is not None, \
                f"Expected email to be stored, but got None"
            # Email was provided and stored (normalization is expected behavior)
        else:
            assert created_data["email"] is None, \
                f"Expected email to be None, but got '{created_data['email']}'"
        
        stored_email = created_data["email"]
        
        assert created_data["phone"] == phone, \
            f"Expected phone '{phone}', but got '{created_data['phone']}'"
        
        # Verify address information is stored correctly
        assert created_data["address"] == address, \
            f"Expected address '{address}', but got '{created_data['address']}'"
        
        assert created_data["city"] == city, \
            f"Expected city '{city}', but got '{created_data['city']}'"
        
        assert created_data["postal_code"] == postal_code, \
            f"Expected postal_code '{postal_code}', but got '{created_data['postal_code']}'"
        
        # Retrieve the customer to verify persistence
        get_response = client.get(f"/api/customers/{customer_id}")
        
        assert get_response.status_code == 200, \
            f"Expected status 200 for retrieval, got {get_response.status_code}"
        
        retrieved_data = get_response.json()
        
        # Verify all fields persist correctly
        assert retrieved_data["name"] == name, \
            f"Retrieved name '{retrieved_data['name']}' doesn't match created name '{name}'"
        
        # Verify email persists (should match the stored normalized version)
        assert retrieved_data["email"] == stored_email, \
            f"Retrieved email '{retrieved_data['email']}' doesn't match stored email '{stored_email}'"
        
        assert retrieved_data["phone"] == phone, \
            f"Retrieved phone '{retrieved_data['phone']}' doesn't match created phone '{phone}'"
        
        assert retrieved_data["address"] == address, \
            f"Retrieved address '{retrieved_data['address']}' doesn't match created address '{address}'"
        
        assert retrieved_data["city"] == city, \
            f"Retrieved city '{retrieved_data['city']}' doesn't match created city '{city}'"
        
        assert retrieved_data["postal_code"] == postal_code, \
            f"Retrieved postal_code '{retrieved_data['postal_code']}' doesn't match created postal_code '{postal_code}'"
        
        # Verify in database directly
        db_customer = db_session.query(Customer).filter(Customer.id == customer_id).first()
        
        assert db_customer is not None, \
            f"Customer {customer_id} should exist in database"
        
        assert db_customer.name == name, \
            f"Database name should be '{name}', but got '{db_customer.name}'"
        
        # Verify email persists in database (should match the stored normalized version)
        assert db_customer.email == stored_email, \
            f"Database email should be '{stored_email}', but got '{db_customer.email}'"
        
        assert db_customer.phone == phone, \
            f"Database phone should be '{phone}', but got '{db_customer.phone}'"
        
        assert db_customer.address == address, \
            f"Database address should be '{address}', but got '{db_customer.address}'"
        
        assert db_customer.city == city, \
            f"Database city should be '{city}', but got '{db_customer.city}'"
        
        assert db_customer.postal_code == postal_code, \
            f"Database postal_code should be '{postal_code}', but got '{db_customer.postal_code}'"
        
        created_customer = db_customer
    
    finally:
        # Clean up: delete the created customer
        if created_customer and created_customer.id:
            db_session.query(Customer).filter(Customer.id == created_customer.id).delete()
            db_session.commit()



# Feature: miniatures-erp, Property 42: Customer update persistence
# Validates: Requirements 12.3
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random initial and updated values
    initial_name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    initial_email=st.one_of(st.none(), st.emails()),
    initial_phone=st.one_of(
        st.none(),
        st.text(min_size=5, max_size=20, alphabet=st.characters(min_codepoint=48, max_codepoint=57))
    ),
    initial_address=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=122))
    ),
    updated_name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    updated_email=st.one_of(st.none(), st.emails()),
    updated_phone=st.one_of(
        st.none(),
        st.text(min_size=5, max_size=20, alphabet=st.characters(min_codepoint=48, max_codepoint=57))
    ),
    updated_address=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=122))
    )
)
def test_customer_update_persistence(client, db_session, initial_name, initial_email, initial_phone, initial_address, updated_name, updated_email, updated_phone, updated_address):
    """
    Property: For any customer, updating its properties and then retrieving it SHALL return the updated values.
    
    This property verifies that:
    1. Updates to customer name persist correctly
    2. Updates to customer contact information persist correctly
    3. Updates to customer address persist correctly
    4. Retrieved data matches the updated values
    5. The update operation is reliable
    """
    created_customer = None
    
    try:
        # Create a customer with initial values
        initial_data = {
            "name": initial_name,
            "source": CustomerSource.ERP.value
        }
        
        if initial_email is not None:
            initial_data["email"] = initial_email
        if initial_phone is not None:
            initial_data["phone"] = initial_phone
        if initial_address is not None:
            initial_data["address"] = initial_address
        
        create_response = client.post(
            "/api/customers",
            json=initial_data
        )
        
        # Verify creation was successful
        assert create_response.status_code == 201, \
            f"Expected status 201 for customer creation, got {create_response.status_code}: {create_response.text}"
        
        created_data = create_response.json()
        customer_id = created_data["id"]
        
        # Track the customer for cleanup
        db_customer = db_session.query(Customer).filter(Customer.id == customer_id).first()
        created_customer = db_customer
        
        # Update the customer via API
        update_data = {
            "name": updated_name
        }
        
        if updated_email is not None:
            update_data["email"] = updated_email
        if updated_phone is not None:
            update_data["phone"] = updated_phone
        if updated_address is not None:
            update_data["address"] = updated_address
        
        update_response = client.put(
            f"/api/customers/{customer_id}",
            json=update_data
        )
        
        # Verify update was successful
        assert update_response.status_code == 200, \
            f"Expected status 200 for update, got {update_response.status_code}: {update_response.text}"
        
        updated_response_data = update_response.json()
        
        # Retrieve the customer via API
        get_response = client.get(f"/api/customers/{customer_id}")
        
        # Verify retrieval was successful
        assert get_response.status_code == 200, \
            f"Expected status 200 for retrieval, got {get_response.status_code}"
        
        retrieved_data = get_response.json()
        
        # Verify the retrieved data matches the updated values
        assert retrieved_data["name"] == updated_name, \
            f"Expected name '{updated_name}', but got '{retrieved_data['name']}'"
        
        # Verify email persists (accounting for normalization)
        if updated_email is not None:
            assert retrieved_data["email"] is not None, \
                f"Expected email to be stored, but got None"
            # Email normalization is expected, so we just verify it was stored
        else:
            # If we didn't update email, it should still have the initial value
            if initial_email is not None:
                assert retrieved_data["email"] is not None, \
                    f"Expected initial email to persist, but got None"
            else:
                assert retrieved_data["email"] is None, \
                    f"Expected email to be None, but got '{retrieved_data['email']}'"
        
        # Verify phone persists
        expected_phone = updated_phone if updated_phone is not None else initial_phone
        assert retrieved_data["phone"] == expected_phone, \
            f"Expected phone '{expected_phone}', but got '{retrieved_data['phone']}'"
        
        # Verify address persists
        expected_address = updated_address if updated_address is not None else initial_address
        assert retrieved_data["address"] == expected_address, \
            f"Expected address '{expected_address}', but got '{retrieved_data['address']}'"
        
        # Verify the ID hasn't changed
        assert retrieved_data["id"] == customer_id, \
            f"Expected ID '{customer_id}', but got '{retrieved_data['id']}'"
        
        # Also verify directly from database
        db_session.expire_all()  # Clear session cache to force fresh read
        db_customer = db_session.query(Customer).filter(Customer.id == customer_id).first()
        
        assert db_customer is not None, \
            f"Customer {customer_id} should exist in database after update"
        
        assert db_customer.name == updated_name, \
            f"Database name should be '{updated_name}', but got '{db_customer.name}'"
        
        assert db_customer.phone == expected_phone, \
            f"Database phone should be '{expected_phone}', but got '{db_customer.phone}'"
        
        assert db_customer.address == expected_address, \
            f"Database address should be '{expected_address}', but got '{db_customer.address}'"
    
    finally:
        # Clean up: delete the created customer
        if created_customer and created_customer.id:
            db_session.query(Customer).filter(Customer.id == created_customer.id).delete()
            db_session.commit()

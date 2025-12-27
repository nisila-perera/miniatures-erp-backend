"""Tests for payment method management"""
import pytest
from decimal import Decimal
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.payment import PaymentMethod
from app.models.enums import CommissionType


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


# Feature: miniatures-erp, Property 26: Payment method creation with required fields
# Validates: Requirements 8.1
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random payment method data
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    commission_type=st.sampled_from([CommissionType.FIXED, CommissionType.PERCENTAGE]),
    commission_value=st.decimals(min_value=Decimal('0'), max_value=Decimal('100'), places=2)
)
def test_payment_method_creation_with_required_fields(client, db_session, name, commission_type, commission_value):
    """
    Property: For any payment method created, it SHALL have both name and commission rate stored.
    
    This property verifies that:
    1. A payment method can be created with name and commission rate
    2. The created payment method stores both name and commission rate
    3. The stored values match the input values
    4. The payment method can be retrieved with all required fields
    """
    created_payment_method = None
    
    try:
        # Create a payment method via API
        create_data = {
            "name": name,
            "commission_type": commission_type.value,
            "commission_value": float(commission_value),
            "is_active": True
        }
        
        create_response = client.post(
            "/api/payment-methods",
            json=create_data
        )
        
        # Verify creation was successful
        assert create_response.status_code == 201, \
            f"Expected status 201 for creation, got {create_response.status_code}"
        
        created_data = create_response.json()
        payment_method_id = created_data["id"]
        
        # Verify the response contains both name and commission rate
        assert "name" in created_data, \
            "Created payment method should have 'name' field"
        assert "commission_type" in created_data, \
            "Created payment method should have 'commission_type' field"
        assert "commission_value" in created_data, \
            "Created payment method should have 'commission_value' field"
        
        # Verify the values match what was sent
        assert created_data["name"] == name, \
            f"Expected name '{name}', but got '{created_data['name']}'"
        assert created_data["commission_type"] == commission_type.value, \
            f"Expected commission_type '{commission_type.value}', but got '{created_data['commission_type']}'"
        assert Decimal(str(created_data["commission_value"])) == commission_value, \
            f"Expected commission_value '{commission_value}', but got '{created_data['commission_value']}'"
        
        # Retrieve the payment method to verify it was stored
        get_response = client.get(f"/api/payment-methods/{payment_method_id}")
        
        assert get_response.status_code == 200, \
            f"Expected status 200 for retrieval, got {get_response.status_code}"
        
        retrieved_data = get_response.json()
        
        # Verify the retrieved data has both name and commission rate
        assert retrieved_data["name"] == name, \
            f"Retrieved name should be '{name}', but got '{retrieved_data['name']}'"
        assert retrieved_data["commission_type"] == commission_type.value, \
            f"Retrieved commission_type should be '{commission_type.value}', but got '{retrieved_data['commission_type']}'"
        assert Decimal(str(retrieved_data["commission_value"])) == commission_value, \
            f"Retrieved commission_value should be '{commission_value}', but got '{retrieved_data['commission_value']}'"
        
        # Verify directly from database
        db_payment_method = db_session.query(PaymentMethod).filter(PaymentMethod.id == payment_method_id).first()
        
        assert db_payment_method is not None, \
            f"Payment method {payment_method_id} should exist in database"
        
        assert db_payment_method.name == name, \
            f"Database name should be '{name}', but got '{db_payment_method.name}'"
        assert db_payment_method.commission_type == commission_type, \
            f"Database commission_type should be '{commission_type}', but got '{db_payment_method.commission_type}'"
        assert db_payment_method.commission_value == commission_value, \
            f"Database commission_value should be '{commission_value}', but got '{db_payment_method.commission_value}'"
        
        created_payment_method = db_payment_method
    
    finally:
        # Clean up: delete the created payment method
        if created_payment_method and created_payment_method.id:
            db_session.query(PaymentMethod).filter(PaymentMethod.id == created_payment_method.id).delete()
            db_session.commit()



# Feature: miniatures-erp, Property 27: Payment method retrieval completeness
# Validates: Requirements 8.3
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate a random number of payment methods to create
    payment_method_count=st.integers(min_value=1, max_value=15),
    name_prefix=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=90))
)
def test_payment_method_retrieval_completeness(client, db_session, payment_method_count, name_prefix):
    """
    Property: For any set of created payment methods, retrieving all methods SHALL return all created methods with their commission rates.
    
    This property verifies that:
    1. All created payment methods are stored in the database
    2. The get_all endpoint returns all payment methods
    3. No payment methods are lost or missing during retrieval
    4. Each payment method includes its commission rate
    5. The count of returned payment methods matches the count of created payment methods
    """
    created_payment_methods = []
    
    try:
        # Create multiple payment methods
        for i in range(payment_method_count):
            # Alternate between fixed and percentage commission types
            commission_type = CommissionType.FIXED if i % 2 == 0 else CommissionType.PERCENTAGE
            commission_value = Decimal('10.00') if commission_type == CommissionType.FIXED else Decimal('5.00')
            
            payment_method = PaymentMethod(
                name=f"{name_prefix}_Method_{i}",
                commission_type=commission_type,
                commission_value=commission_value,
                is_active=True
            )
            db_session.add(payment_method)
            db_session.flush()  # Flush to generate ID
            created_payment_methods.append(payment_method)
        
        db_session.commit()
        
        # Retrieve all payment methods via API
        response = client.get("/api/payment-methods")
        
        # Verify response is successful
        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"
        
        retrieved_data = response.json()
        
        # Extract IDs from created payment methods
        created_ids = {str(pm.id) for pm in created_payment_methods}
        
        # Extract IDs from retrieved payment methods
        retrieved_ids = {pm["id"] for pm in retrieved_data}
        
        # Verify all created payment methods are in the retrieved set
        missing_ids = created_ids - retrieved_ids
        assert len(missing_ids) == 0, \
            f"Expected all {len(created_ids)} created payment methods to be retrieved, but {len(missing_ids)} are missing: {missing_ids}"
        
        # Verify each created payment method is present in the retrieved data with commission rate
        for created_pm in created_payment_methods:
            matching_pms = [pm for pm in retrieved_data if pm["id"] == str(created_pm.id)]
            assert len(matching_pms) == 1, \
                f"Expected exactly 1 match for payment method {created_pm.id}, found {len(matching_pms)}"
            
            # Verify the data matches including commission rate
            matching_pm = matching_pms[0]
            assert matching_pm["name"] == created_pm.name, \
                f"Expected name '{created_pm.name}', got '{matching_pm['name']}'"
            assert matching_pm["commission_type"] == created_pm.commission_type.value, \
                f"Expected commission_type '{created_pm.commission_type.value}', got '{matching_pm['commission_type']}'"
            assert Decimal(str(matching_pm["commission_value"])) == created_pm.commission_value, \
                f"Expected commission_value '{created_pm.commission_value}', got '{matching_pm['commission_value']}'"
            
            # Verify commission rate is present
            assert "commission_type" in matching_pm, \
                f"Payment method {created_pm.id} should have 'commission_type' field"
            assert "commission_value" in matching_pm, \
                f"Payment method {created_pm.id} should have 'commission_value' field"
    
    finally:
        # Clean up: delete all created payment methods
        for payment_method in created_payment_methods:
            if payment_method.id:
                db_session.query(PaymentMethod).filter(PaymentMethod.id == payment_method.id).delete()
        db_session.commit()



# Feature: miniatures-erp, Property 28: Payment method update persistence
# Validates: Requirements 8.4
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random initial and updated values
    initial_name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    initial_commission_type=st.sampled_from([CommissionType.FIXED, CommissionType.PERCENTAGE]),
    initial_commission_value=st.decimals(min_value=Decimal('0'), max_value=Decimal('100'), places=2),
    updated_name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    updated_commission_type=st.sampled_from([CommissionType.FIXED, CommissionType.PERCENTAGE]),
    updated_commission_value=st.decimals(min_value=Decimal('0'), max_value=Decimal('100'), places=2)
)
def test_payment_method_update_persistence(client, db_session, initial_name, initial_commission_type, 
                                          initial_commission_value, updated_name, updated_commission_type, 
                                          updated_commission_value):
    """
    Property: For any payment method, updating its properties and then retrieving it SHALL return the updated values.
    
    This property verifies that:
    1. Updates to payment method name persist correctly
    2. Updates to commission type persist correctly
    3. Updates to commission value persist correctly
    4. Retrieved data matches the updated values
    5. The update operation is idempotent and reliable
    """
    created_payment_method = None
    
    try:
        # Create a payment method with initial values
        payment_method = PaymentMethod(
            name=initial_name,
            commission_type=initial_commission_type,
            commission_value=initial_commission_value,
            is_active=True
        )
        db_session.add(payment_method)
        db_session.commit()
        db_session.refresh(payment_method)
        created_payment_method = payment_method
        payment_method_id = str(payment_method.id)
        
        # Update the payment method via API
        update_data = {
            "name": updated_name,
            "commission_type": updated_commission_type.value,
            "commission_value": float(updated_commission_value)
        }
        
        update_response = client.put(
            f"/api/payment-methods/{payment_method_id}",
            json=update_data
        )
        
        # Verify update was successful
        assert update_response.status_code == 200, \
            f"Expected status 200 for update, got {update_response.status_code}"
        
        # Retrieve the payment method via API
        get_response = client.get(f"/api/payment-methods/{payment_method_id}")
        
        # Verify retrieval was successful
        assert get_response.status_code == 200, \
            f"Expected status 200 for retrieval, got {get_response.status_code}"
        
        retrieved_data = get_response.json()
        
        # Verify the retrieved data matches the updated values
        assert retrieved_data["name"] == updated_name, \
            f"Expected name '{updated_name}', but got '{retrieved_data['name']}'"
        
        assert retrieved_data["commission_type"] == updated_commission_type.value, \
            f"Expected commission_type '{updated_commission_type.value}', but got '{retrieved_data['commission_type']}'"
        
        assert Decimal(str(retrieved_data["commission_value"])) == updated_commission_value, \
            f"Expected commission_value '{updated_commission_value}', but got '{retrieved_data['commission_value']}'"
        
        # Verify the ID hasn't changed
        assert retrieved_data["id"] == payment_method_id, \
            f"Expected ID '{payment_method_id}', but got '{retrieved_data['id']}'"
        
        # Also verify directly from database
        db_session.expire_all()  # Clear session cache to force fresh read
        db_payment_method = db_session.query(PaymentMethod).filter(PaymentMethod.id == payment_method_id).first()
        
        assert db_payment_method is not None, \
            f"Payment method {payment_method_id} should exist in database after update"
        
        assert db_payment_method.name == updated_name, \
            f"Database name should be '{updated_name}', but got '{db_payment_method.name}'"
        
        assert db_payment_method.commission_type == updated_commission_type, \
            f"Database commission_type should be '{updated_commission_type}', but got '{db_payment_method.commission_type}'"
        
        assert db_payment_method.commission_value == updated_commission_value, \
            f"Database commission_value should be '{updated_commission_value}', but got '{db_payment_method.commission_value}'"
    
    finally:
        # Clean up: delete the created payment method
        if created_payment_method and created_payment_method.id:
            db_session.query(PaymentMethod).filter(PaymentMethod.id == created_payment_method.id).delete()
            db_session.commit()



# Feature: miniatures-erp, Property 29: Payment method deletion
# Validates: Requirements 8.5
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random number of payment methods to create and delete
    payment_method_count=st.integers(min_value=1, max_value=10),
    delete_index=st.integers(min_value=0, max_value=9),  # Will be modded by payment_method_count
    name_prefix=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=90))
)
def test_payment_method_deletion(client, db_session, payment_method_count, delete_index, name_prefix):
    """
    Property: For any payment method, after deletion, retrieving all methods SHALL not include the deleted method.
    
    This property verifies that:
    1. A payment method can be successfully deleted
    2. After deletion, the payment method is not returned in the list of all payment methods
    3. The deleted payment method cannot be retrieved by ID
    4. Other payment methods remain unaffected by the deletion
    """
    created_payment_methods = []
    
    try:
        # Create multiple payment methods
        for i in range(payment_method_count):
            commission_type = CommissionType.FIXED if i % 2 == 0 else CommissionType.PERCENTAGE
            commission_value = Decimal('15.00') if commission_type == CommissionType.FIXED else Decimal('7.50')
            
            payment_method = PaymentMethod(
                name=f"{name_prefix}_Method_{i}",
                commission_type=commission_type,
                commission_value=commission_value,
                is_active=True
            )
            db_session.add(payment_method)
            db_session.flush()  # Flush to generate ID
            created_payment_methods.append(payment_method)
        
        db_session.commit()
        
        # Select a payment method to delete (use modulo to ensure valid index)
        delete_idx = delete_index % payment_method_count
        payment_method_to_delete = created_payment_methods[delete_idx]
        deleted_payment_method_id = str(payment_method_to_delete.id)
        deleted_payment_method_name = payment_method_to_delete.name
        
        # Get all payment methods before deletion
        response_before = client.get("/api/payment-methods")
        assert response_before.status_code == 200
        payment_methods_before = response_before.json()
        
        # Verify the payment method exists before deletion
        payment_method_ids_before = {pm["id"] for pm in payment_methods_before}
        assert deleted_payment_method_id in payment_method_ids_before, \
            f"Payment method {deleted_payment_method_id} should exist before deletion"
        
        # Delete the payment method via API
        delete_response = client.delete(f"/api/payment-methods/{deleted_payment_method_id}")
        
        # Verify deletion was successful
        assert delete_response.status_code == 204, \
            f"Expected status 204 for deletion, got {delete_response.status_code}"
        
        # Get all payment methods after deletion
        response_after = client.get("/api/payment-methods")
        assert response_after.status_code == 200
        payment_methods_after = response_after.json()
        
        # Extract IDs from retrieved payment methods after deletion
        payment_method_ids_after = {pm["id"] for pm in payment_methods_after}
        
        # Verify the deleted payment method is NOT in the retrieved set
        assert deleted_payment_method_id not in payment_method_ids_after, \
            f"Deleted payment method {deleted_payment_method_id} should not be in the list of all payment methods"
        
        # Verify the deleted payment method cannot be retrieved by ID
        get_deleted_response = client.get(f"/api/payment-methods/{deleted_payment_method_id}")
        assert get_deleted_response.status_code == 404, \
            f"Expected status 404 when retrieving deleted payment method, got {get_deleted_response.status_code}"
        
        # Verify the deleted payment method is not in the database
        db_payment_method = db_session.query(PaymentMethod).filter(PaymentMethod.id == deleted_payment_method_id).first()
        assert db_payment_method is None, \
            f"Deleted payment method {deleted_payment_method_id} should not exist in the database"
        
        # Verify other payment methods still exist (if there were any)
        if payment_method_count > 1:
            remaining_payment_method_ids = [str(pm.id) for i, pm in enumerate(created_payment_methods) if i != delete_idx]
            for remaining_id in remaining_payment_method_ids:
                assert remaining_id in payment_method_ids_after, \
                    f"Non-deleted payment method {remaining_id} should still exist after deletion"
        
        # Verify each remaining payment method is present
        for i, pm in enumerate(created_payment_methods):
            if i != delete_idx:
                assert str(pm.id) in payment_method_ids_after, \
                    f"Payment method {pm.id} (index {i}) should still exist after deleting payment method at index {delete_idx}"
        
        # Remove the deleted payment method from our tracking list
        created_payment_methods.pop(delete_idx)
    
    finally:
        # Clean up: delete all remaining created payment methods
        for payment_method in created_payment_methods:
            if payment_method.id:
                try:
                    db_session.query(PaymentMethod).filter(PaymentMethod.id == payment_method.id).delete()
                except:
                    pass  # Payment method might already be deleted
        db_session.commit()



# Feature: miniatures-erp, Property 30: Payment commission calculation
# Validates: Requirements 8.6
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random payment method and amount
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    commission_type=st.sampled_from([CommissionType.FIXED, CommissionType.PERCENTAGE]),
    commission_value=st.decimals(min_value=Decimal('0.01'), max_value=Decimal('100'), places=2),
    payment_amount=st.decimals(min_value=Decimal('1.00'), max_value=Decimal('10000.00'), places=2)
)
def test_payment_commission_calculation(db_session, name, commission_type, commission_value, payment_amount):
    """
    Property: For any payment with a payment method, the commission amount SHALL be calculated based on the payment method's commission type and rate.
    
    This property verifies that:
    1. Fixed commission returns the fixed commission value
    2. Percentage commission calculates correctly as (amount * percentage / 100)
    3. Commission calculation is accurate for all valid inputs
    4. The calculation logic is consistent and reliable
    """
    from app.services.payment_method import PaymentMethodService
    
    created_payment_method = None
    
    try:
        # Create a payment method
        payment_method = PaymentMethod(
            name=name,
            commission_type=commission_type,
            commission_value=commission_value,
            is_active=True
        )
        db_session.add(payment_method)
        db_session.commit()
        db_session.refresh(payment_method)
        created_payment_method = payment_method
        
        # Calculate commission using the service
        service = PaymentMethodService(db_session)
        calculated_commission = service.calculate_commission(str(payment_method.id), payment_amount)
        
        # Verify the commission calculation based on type
        if commission_type == CommissionType.FIXED:
            # For fixed commission, the commission should equal the fixed value
            expected_commission = commission_value
            assert calculated_commission == expected_commission, \
                f"For FIXED commission, expected {expected_commission}, but got {calculated_commission}"
        else:  # PERCENTAGE
            # For percentage commission, calculate: (amount * percentage / 100)
            expected_commission = (payment_amount * commission_value) / Decimal('100')
            # Round to 2 decimal places for comparison
            expected_commission = expected_commission.quantize(Decimal('0.01'))
            calculated_commission = calculated_commission.quantize(Decimal('0.01'))
            
            assert calculated_commission == expected_commission, \
                f"For PERCENTAGE commission of {commission_value}% on amount {payment_amount}, expected {expected_commission}, but got {calculated_commission}"
        
        # Verify the commission is non-negative
        assert calculated_commission >= 0, \
            f"Commission should be non-negative, but got {calculated_commission}"
        
        # For percentage commission, verify it doesn't exceed the payment amount
        if commission_type == CommissionType.PERCENTAGE:
            assert calculated_commission <= payment_amount, \
                f"Percentage commission {calculated_commission} should not exceed payment amount {payment_amount}"
    
    finally:
        # Clean up: delete the created payment method
        if created_payment_method and created_payment_method.id:
            db_session.query(PaymentMethod).filter(PaymentMethod.id == created_payment_method.id).delete()
            db_session.commit()

"""Property-based tests for payment management"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.payment import Payment, PaymentMethod
from app.models.order import Order, OrderItem
from app.models.customer import Customer
from app.models.product import ProductCategory
from app.models.enums import OrderSource, OrderStatus, CommissionType


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
def test_customer(db_session):
    """Create a test customer for orders"""
    customer = Customer(
        name="Test Customer",
        email="test@example.com",
        phone="1234567890",
        address="123 Test St",
        city="Test City",
        postal_code="12345",
        source="erp"
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    yield customer


@pytest.fixture
def test_category(db_session):
    """Create a test product category"""
    category = ProductCategory(
        name="Test Category",
        description="Test category"
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    yield category


@pytest.fixture
def test_payment_method(db_session):
    """Create a test payment method"""
    payment_method = PaymentMethod(
        name="Test Payment Method",
        commission_type=CommissionType.FIXED,
        commission_value=Decimal('5.00'),
        is_active=True
    )
    db_session.add(payment_method)
    db_session.commit()
    db_session.refresh(payment_method)
    yield payment_method


# Feature: miniatures-erp, Property 31: Order balance calculation
# Validates: Requirements 9.4
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random order total and payment amounts
    order_total=st.decimals(min_value=Decimal('10.00'), max_value=Decimal('10000.00'), places=2),
    payment_count=st.integers(min_value=1, max_value=5),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_order_balance_calculation(client, db_session, test_customer, test_category, test_payment_method,
                                   order_total, payment_count, seed):
    """
    Property: For any order with payments, the remaining balance SHALL equal the total amount minus the sum of all payment amounts.
    
    This property verifies that:
    1. The balance is calculated correctly as total_amount - sum(payments)
    2. The balance updates correctly after each payment
    3. The balance calculation is accurate for multiple payments
    4. The balance is always consistent with the order total and payments
    """
    import random
    random.seed(seed)
    
    created_order = None
    created_payments = []
    
    try:
        # Create an order with the specified total
        order = Order(
            order_number=f"TEST-{seed}",
            source=OrderSource.CUSTOM,
            status=OrderStatus.PENDING,
            customer_id=test_customer.id,
            order_date=datetime.utcnow(),
            subtotal=order_total,
            total_amount=order_total,
            paid_amount=Decimal('0'),
            balance=order_total,
            is_fully_paid=False
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        created_order = order
        
        # Generate random payment amounts that sum to less than or equal to order total
        # This ensures we can make valid payments
        remaining_amount = order_total
        payment_amounts = []
        
        for i in range(payment_count):
            if i == payment_count - 1:
                # Last payment: use remaining amount or a portion of it
                max_payment = remaining_amount
            else:
                # Not last payment: use a portion of remaining amount
                max_payment = remaining_amount / Decimal(str(payment_count - i))
            
            # Generate a random payment amount between 1 and max_payment
            if max_payment >= Decimal('1.00'):
                payment_amount = Decimal(str(random.uniform(1.00, float(max_payment))))
                payment_amount = payment_amount.quantize(Decimal('0.01'))
                payment_amounts.append(payment_amount)
                remaining_amount -= payment_amount
            else:
                break
        
        # Make payments and verify balance after each
        total_paid = Decimal('0')
        
        for i, payment_amount in enumerate(payment_amounts):
            # Create payment
            payment_data = {
                "order_id": str(order.id),
                "payment_method_id": str(test_payment_method.id),
                "amount": float(payment_amount),
                "payment_date": date.today().isoformat(),
                "notes": f"Test payment {i+1}"
            }
            
            response = client.post(
                f"/api/orders/{order.id}/payments",
                json=payment_data
            )
            
            assert response.status_code == 201, \
                f"Expected status 201 for payment creation, got {response.status_code}: {response.text}"
            
            payment_response = response.json()
            created_payments.append(payment_response["id"])
            
            # Update total paid
            total_paid += payment_amount
            
            # Retrieve the order to check balance
            order_response = client.get(f"/api/orders/{order.id}")
            assert order_response.status_code == 200
            
            order_data = order_response.json()
            
            # Verify balance calculation
            expected_balance = order_total - total_paid
            actual_balance = Decimal(str(order_data["balance"]))
            
            # Allow for small rounding differences
            balance_diff = abs(expected_balance - actual_balance)
            assert balance_diff < Decimal('0.01'), \
                f"After payment {i+1}, expected balance {expected_balance}, but got {actual_balance}. " \
                f"Order total: {order_total}, Total paid: {total_paid}"
            
            # Verify paid_amount is correct
            expected_paid = total_paid
            actual_paid = Decimal(str(order_data["paid_amount"]))
            
            paid_diff = abs(expected_paid - actual_paid)
            assert paid_diff < Decimal('0.01'), \
                f"After payment {i+1}, expected paid_amount {expected_paid}, but got {actual_paid}"
        
        # Final verification: balance should equal total - sum of all payments
        final_order_response = client.get(f"/api/orders/{order.id}")
        assert final_order_response.status_code == 200
        
        final_order_data = final_order_response.json()
        final_balance = Decimal(str(final_order_data["balance"]))
        final_paid = Decimal(str(final_order_data["paid_amount"]))
        
        expected_final_balance = order_total - total_paid
        balance_diff = abs(expected_final_balance - final_balance)
        
        assert balance_diff < Decimal('0.01'), \
            f"Final balance should be {expected_final_balance}, but got {final_balance}. " \
            f"Order total: {order_total}, Total paid: {total_paid}"
        
        # Verify the relationship: total_amount = paid_amount + balance
        calculated_total = final_paid + final_balance
        total_diff = abs(order_total - calculated_total)
        
        assert total_diff < Decimal('0.01'), \
            f"Total amount ({order_total}) should equal paid_amount ({final_paid}) + balance ({final_balance}) = {calculated_total}"
    
    finally:
        # Clean up: delete payments and order
        for payment_id in created_payments:
            try:
                db_session.query(Payment).filter(Payment.id == payment_id).delete()
            except:
                pass
        
        if created_order and created_order.id:
            try:
                db_session.query(Order).filter(Order.id == created_order.id).delete()
            except:
                pass
        
        db_session.commit()


# Feature: miniatures-erp, Property 32: Fully paid flag
# Validates: Requirements 9.7
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random order total
    order_total=st.decimals(min_value=Decimal('10.00'), max_value=Decimal('1000.00'), places=2),
    overpayment=st.booleans(),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_fully_paid_flag(client, db_session, test_customer, test_category, test_payment_method,
                        order_total, overpayment, seed):
    """
    Property: For any order, when the sum of payments equals the total amount, the order SHALL be marked as fully paid.
    
    This property verifies that:
    1. is_fully_paid is False when balance > 0
    2. is_fully_paid is True when balance <= 0
    3. is_fully_paid is True when payments equal total
    4. is_fully_paid is True when payments exceed total (overpayment)
    5. The flag updates correctly as payments are made
    """
    import random
    random.seed(seed)
    
    created_order = None
    created_payments = []
    
    try:
        # Create an order with the specified total
        order = Order(
            order_number=f"TEST-FP-{seed}",
            source=OrderSource.CUSTOM,
            status=OrderStatus.PENDING,
            customer_id=test_customer.id,
            order_date=datetime.utcnow(),
            subtotal=order_total,
            total_amount=order_total,
            paid_amount=Decimal('0'),
            balance=order_total,
            is_fully_paid=False
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        created_order = order
        
        # Verify initial state: not fully paid
        order_response = client.get(f"/api/orders/{order.id}")
        assert order_response.status_code == 200
        order_data = order_response.json()
        
        assert order_data["is_fully_paid"] is False, \
            "Order should not be fully paid initially"
        assert Decimal(str(order_data["balance"])) == order_total, \
            f"Initial balance should be {order_total}"
        
        # Make a partial payment (50% of total)
        partial_amount = (order_total / Decimal('2')).quantize(Decimal('0.01'))
        
        payment_data = {
            "order_id": str(order.id),
            "payment_method_id": str(test_payment_method.id),
            "amount": float(partial_amount),
            "payment_date": date.today().isoformat(),
            "notes": "Partial payment"
        }
        
        response = client.post(
            f"/api/orders/{order.id}/payments",
            json=payment_data
        )
        
        assert response.status_code == 201
        created_payments.append(response.json()["id"])
        
        # Verify still not fully paid after partial payment
        order_response = client.get(f"/api/orders/{order.id}")
        assert order_response.status_code == 200
        order_data = order_response.json()
        
        assert order_data["is_fully_paid"] is False, \
            "Order should not be fully paid after partial payment"
        
        remaining_balance = Decimal(str(order_data["balance"]))
        assert remaining_balance > 0, \
            f"Balance should be positive after partial payment, got {remaining_balance}"
        
        # Make final payment (remaining balance or more if overpayment)
        if overpayment:
            # Pay more than remaining balance
            final_amount = remaining_balance + Decimal('10.00')
        else:
            # Pay exactly the remaining balance
            final_amount = remaining_balance
        
        payment_data = {
            "order_id": str(order.id),
            "payment_method_id": str(test_payment_method.id),
            "amount": float(final_amount),
            "payment_date": date.today().isoformat(),
            "notes": "Final payment"
        }
        
        response = client.post(
            f"/api/orders/{order.id}/payments",
            json=payment_data
        )
        
        assert response.status_code == 201
        created_payments.append(response.json()["id"])
        
        # Verify order is now fully paid
        order_response = client.get(f"/api/orders/{order.id}")
        assert order_response.status_code == 200
        order_data = order_response.json()
        
        assert order_data["is_fully_paid"] is True, \
            f"Order should be fully paid after final payment. " \
            f"Total: {order_total}, Paid: {order_data['paid_amount']}, Balance: {order_data['balance']}"
        
        final_balance = Decimal(str(order_data["balance"]))
        assert final_balance <= 0, \
            f"Balance should be <= 0 when fully paid, got {final_balance}"
        
        # Verify the paid amount
        total_paid = partial_amount + final_amount
        actual_paid = Decimal(str(order_data["paid_amount"]))
        
        paid_diff = abs(total_paid - actual_paid)
        assert paid_diff < Decimal('0.01'), \
            f"Expected paid_amount {total_paid}, but got {actual_paid}"
    
    finally:
        # Clean up: delete payments and order
        for payment_id in created_payments:
            try:
                db_session.query(Payment).filter(Payment.id == payment_id).delete()
            except:
                pass
        
        if created_order and created_order.id:
            try:
                db_session.query(Order).filter(Order.id == created_order.id).delete()
            except:
                pass
        
        db_session.commit()

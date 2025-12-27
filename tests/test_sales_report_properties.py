"""Property-based tests for sales reporting"""
import pytest
import uuid
from decimal import Decimal
from datetime import date, datetime, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.order import Order
from app.models.customer import Customer
from app.models.product import Product, ProductCategory
from app.models.payment import Payment, PaymentMethod
from app.models.enums import OrderSource, OrderStatus, ProductSource, CustomerSource, CommissionType


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


def create_test_customer(db_session, seed: int) -> Customer:
    """Helper to create a test customer"""
    customer = Customer(
        name=f"Test Customer {seed}",
        email=f"customer{seed}@test.com",
        phone=f"555-{seed:04d}",
        address=f"{seed} Test St",
        city="Test City",
        postal_code=f"{seed:05d}",
        source=CustomerSource.ERP
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


def create_test_category(db_session, seed: int) -> ProductCategory:
    """Helper to create a test product category"""
    category = ProductCategory(
        name=f"Test Category {seed}",
        description=f"Test category description {seed}"
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


def create_test_payment_method(db_session, seed: int) -> PaymentMethod:
    """Helper to create a test payment method"""
    payment_method = PaymentMethod(
        name=f"Test Payment Method {seed}",
        commission_type=CommissionType.PERCENTAGE,
        commission_value=Decimal('2.5'),
        is_active=True
    )
    db_session.add(payment_method)
    db_session.commit()
    db_session.refresh(payment_method)
    return payment_method


# Feature: miniatures-erp, Property 45: Sales report total calculation
# Validates: Requirements 14.4
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate a list of order amounts
    order_amounts=st.lists(
        st.decimals(min_value=Decimal('1.00'), max_value=Decimal('1000.00'), places=2),
        min_size=1,
        max_size=10
    ),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_sales_report_total_calculation(client, db_session, order_amounts, seed):
    """
    Property: For any sales report for a given period, the total sales amount SHALL equal 
    the sum of all order totals in that period.
    
    This property verifies that:
    1. The sales report correctly sums all order totals
    2. No orders are missed or double-counted
    3. The calculation is accurate for any number of orders
    """
    # Create test data
    customer = create_test_customer(db_session, seed)
    category = create_test_category(db_session, seed)
    
    # Create orders with the generated amounts
    today = date.today()
    created_orders = []
    
    # Use UUID to ensure unique order numbers across all test runs
    unique_id = uuid.uuid4().hex[:8]
    for i, amount in enumerate(order_amounts):
        order = Order(
            order_number=f"ORD-{unique_id}-{i}",
            source=OrderSource.CUSTOM,
            status=OrderStatus.PENDING,
            customer_id=customer.id,
            order_date=datetime.combine(today, datetime.min.time()),
            subtotal=amount,
            total_amount=amount,
            paid_amount=Decimal('0'),
            balance=amount,
            is_fully_paid=False
        )
        db_session.add(order)
        created_orders.append(order)
    
    db_session.commit()
    
    # Calculate expected total
    expected_total = sum(order_amounts)
    
    # Request sales report for today
    report_request = {
        "date_range": "today",
        "group_by_category": False,
        "group_by_payment_method": False
    }
    
    response = client.post("/api/reports/sales", json=report_request)
    
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text}"
    
    report = response.json()
    
    # Verify the total sales matches the sum of all order amounts
    actual_total = Decimal(str(report["total_sales"]))
    
    assert actual_total == expected_total, \
        f"Sales report total {actual_total} does not match expected sum {expected_total}"
    
    # Clean up
    for order in created_orders:
        db_session.delete(order)
    db_session.delete(category)
    db_session.delete(customer)
    db_session.commit()


# Feature: miniatures-erp, Property 46: Sales report order count
# Validates: Requirements 14.5
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate a random number of orders
    num_orders=st.integers(min_value=1, max_value=20),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_sales_report_order_count(client, db_session, num_orders, seed):
    """
    Property: For any sales report for a given period, the order count SHALL equal 
    the number of orders in that period.
    
    This property verifies that:
    1. The sales report correctly counts all orders
    2. No orders are missed or double-counted
    3. The count is accurate for any number of orders
    """
    # Create test data
    customer = create_test_customer(db_session, seed)
    category = create_test_category(db_session, seed)
    
    # Create the specified number of orders
    today = date.today()
    created_orders = []
    
    # Use UUID to ensure unique order numbers across all test runs
    unique_id = uuid.uuid4().hex[:8]
    for i in range(num_orders):
        order = Order(
            order_number=f"ORD-{unique_id}-{i}",
            source=OrderSource.CUSTOM,
            status=OrderStatus.PENDING,
            customer_id=customer.id,
            order_date=datetime.combine(today, datetime.min.time()),
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            paid_amount=Decimal('0'),
            balance=Decimal('100.00'),
            is_fully_paid=False
        )
        db_session.add(order)
        created_orders.append(order)
    
    db_session.commit()
    
    # Request sales report for today
    report_request = {
        "date_range": "today",
        "group_by_category": False,
        "group_by_payment_method": False
    }
    
    response = client.post("/api/reports/sales", json=report_request)
    
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text}"
    
    report = response.json()
    
    # Verify the order count matches the number of orders created
    actual_count = report["order_count"]
    
    assert actual_count == num_orders, \
        f"Sales report order count {actual_count} does not match expected count {num_orders}"
    
    # Clean up
    for order in created_orders:
        db_session.delete(order)
    db_session.delete(category)
    db_session.delete(customer)
    db_session.commit()


# Feature: miniatures-erp, Property 47: Sales report average calculation
# Validates: Requirements 14.6
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate a list of order amounts
    order_amounts=st.lists(
        st.decimals(min_value=Decimal('1.00'), max_value=Decimal('1000.00'), places=2),
        min_size=1,
        max_size=10
    ),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_sales_report_average_calculation(client, db_session, order_amounts, seed):
    """
    Property: For any sales report, the average order value SHALL equal 
    total sales divided by order count.
    
    This property verifies that:
    1. The average is calculated correctly
    2. The calculation handles division properly
    3. The average is accurate for any set of order amounts
    """
    # Create test data
    customer = create_test_customer(db_session, seed)
    category = create_test_category(db_session, seed)
    
    # Create orders with the generated amounts
    today = date.today()
    created_orders = []
    
    # Use UUID to ensure unique order numbers across all test runs
    unique_id = uuid.uuid4().hex[:8]
    for i, amount in enumerate(order_amounts):
        order = Order(
            order_number=f"ORD-{unique_id}-{i}",
            source=OrderSource.CUSTOM,
            status=OrderStatus.PENDING,
            customer_id=customer.id,
            order_date=datetime.combine(today, datetime.min.time()),
            subtotal=amount,
            total_amount=amount,
            paid_amount=Decimal('0'),
            balance=amount,
            is_fully_paid=False
        )
        db_session.add(order)
        created_orders.append(order)
    
    db_session.commit()
    
    # Calculate expected average
    expected_total = sum(order_amounts)
    expected_count = len(order_amounts)
    expected_average = expected_total / expected_count
    
    # Request sales report for today
    report_request = {
        "date_range": "today",
        "group_by_category": False,
        "group_by_payment_method": False
    }
    
    response = client.post("/api/reports/sales", json=report_request)
    
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text}"
    
    report = response.json()
    
    # Verify the average order value is calculated correctly
    actual_average = Decimal(str(report["average_order_value"]))
    
    # Allow for small rounding differences
    difference = abs(actual_average - expected_average)
    assert difference < Decimal('0.01'), \
        f"Sales report average {actual_average} does not match expected average {expected_average} (difference: {difference})"
    
    # Clean up
    for order in created_orders:
        db_session.delete(order)
    db_session.delete(category)
    db_session.delete(customer)
    db_session.commit()

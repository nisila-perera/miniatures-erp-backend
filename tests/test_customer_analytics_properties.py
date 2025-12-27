"""Property-based tests for customer analytics reporting"""
import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.order import Order
from app.models.customer import Customer
from app.models.product import ProductCategory
from app.models.enums import OrderSource, OrderStatus, CustomerSource


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


# Feature: miniatures-erp, Property 56: Customer analytics count
# Validates: Requirements 18.1
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate a random number of customers
    num_customers=st.integers(min_value=1, max_value=20),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_customer_analytics_count(client, db_session, num_customers, seed):
    """
    Property: For any customer analytics report, the total customer count SHALL equal 
    the number of customers in the system.
    
    This property verifies that:
    1. The customer analytics report correctly counts all customers
    2. No customers are missed or double-counted
    3. The count is accurate for any number of customers
    """
    # Create the specified number of customers
    created_customers = []
    
    for i in range(num_customers):
        customer = create_test_customer(db_session, seed + i)
        created_customers.append(customer)
    
    # Request customer analytics report for today
    report_request = {
        "date_range": "today"
    }
    
    response = client.post("/api/reports/customer-analytics", json=report_request)
    
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text}"
    
    report = response.json()
    
    # Verify the total customer count matches the number of customers created
    actual_count = report["total_customers"]
    
    assert actual_count == num_customers, \
        f"Customer analytics total count {actual_count} does not match expected count {num_customers}"
    
    # Clean up
    for customer in created_customers:
        db_session.delete(customer)
    db_session.commit()


# Feature: miniatures-erp, Property 57: Customer analytics average order value
# Validates: Requirements 18.2
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate customers with orders
    customer_orders=st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=5),  # number of orders per customer
            st.decimals(min_value=Decimal('10.00'), max_value=Decimal('500.00'), places=2)  # order amount
        ),
        min_size=1,
        max_size=10
    ),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_customer_analytics_average_order_value(client, db_session, customer_orders, seed):
    """
    Property: For any customer analytics report, the average order value per customer SHALL 
    be calculated correctly as total revenue divided by total customers with orders.
    
    This property verifies that:
    1. The average order value per customer is calculated correctly
    2. The calculation handles division properly
    3. The average is accurate for any set of customers and orders
    """
    # Create test data
    category = create_test_category(db_session, seed)
    created_customers = []
    created_orders = []
    today = date.today()
    
    total_revenue = Decimal('0')
    
    for i, (num_orders, order_amount) in enumerate(customer_orders):
        customer = create_test_customer(db_session, seed + i)
        created_customers.append(customer)
        
        # Create orders for this customer
        for j in range(num_orders):
            order = Order(
                order_number=f"ORD-{seed}-{i}-{j}",
                source=OrderSource.CUSTOM,
                status=OrderStatus.PENDING,
                customer_id=customer.id,
                order_date=datetime.combine(today, datetime.min.time()),
                subtotal=order_amount,
                total_amount=order_amount,
                paid_amount=Decimal('0'),
                balance=order_amount,
                is_fully_paid=False
            )
            db_session.add(order)
            created_orders.append(order)
            total_revenue += order_amount
    
    db_session.commit()
    
    # Calculate expected average order value per customer
    customers_with_orders = len(customer_orders)
    expected_average = total_revenue / customers_with_orders if customers_with_orders > 0 else Decimal('0')
    
    # Request customer analytics report for today
    report_request = {
        "date_range": "today"
    }
    
    response = client.post("/api/reports/customer-analytics", json=report_request)
    
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text}"
    
    report = response.json()
    
    # Verify the average order value per customer is calculated correctly
    actual_average = Decimal(str(report["average_order_value_per_customer"]))
    
    # Allow for small rounding differences
    difference = abs(actual_average - expected_average)
    assert difference < Decimal('0.01'), \
        f"Customer analytics average {actual_average} does not match expected average {expected_average} (difference: {difference})"
    
    # Clean up
    for order in created_orders:
        db_session.delete(order)
    for customer in created_customers:
        db_session.delete(customer)
    db_session.delete(category)
    db_session.commit()


# Feature: miniatures-erp, Property 58: Customer analytics repeat rate
# Validates: Requirements 18.3
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(
    # Generate customers with varying order counts
    customer_order_counts=st.lists(
        st.integers(min_value=1, max_value=5),  # number of orders per customer
        min_size=2,
        max_size=10
    ),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_customer_analytics_repeat_rate(client, db_session, customer_order_counts, seed):
    """
    Property: For any customer analytics report, the repeat customer rate SHALL equal 
    the number of customers with more than one order divided by total customers.
    
    This property verifies that:
    1. The repeat customer rate is calculated correctly
    2. Only customers with more than one order are counted as repeat customers
    3. The rate is expressed as a percentage
    """
    # Create test data
    category = create_test_category(db_session, seed)
    created_customers = []
    created_orders = []
    today = date.today()
    
    repeat_customer_count = 0
    
    for i, num_orders in enumerate(customer_order_counts):
        customer = create_test_customer(db_session, seed + i)
        created_customers.append(customer)
        
        # Count repeat customers (more than 1 order)
        if num_orders > 1:
            repeat_customer_count += 1
        
        # Create orders for this customer
        for j in range(num_orders):
            order = Order(
                order_number=f"ORD-{seed}-{i}-{j}",
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
    
    # Calculate expected repeat customer rate
    total_customers = len(customer_order_counts)
    expected_rate = (Decimal(repeat_customer_count) / Decimal(total_customers) * Decimal(100)) if total_customers > 0 else Decimal('0')
    
    # Request customer analytics report for today
    report_request = {
        "date_range": "today"
    }
    
    response = client.post("/api/reports/customer-analytics", json=report_request)
    
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text}"
    
    report = response.json()
    
    # Verify the repeat customer rate is calculated correctly
    actual_rate = Decimal(str(report["repeat_customer_rate"]))
    
    # Allow for small rounding differences
    difference = abs(actual_rate - expected_rate)
    assert difference < Decimal('0.01'), \
        f"Customer analytics repeat rate {actual_rate}% does not match expected rate {expected_rate}% (difference: {difference})"
    
    # Clean up
    for order in created_orders:
        db_session.delete(order)
    for customer in created_customers:
        db_session.delete(customer)
    db_session.delete(category)
    db_session.commit()


# Feature: miniatures-erp, Property 59: Customer analytics top customers ranking
# Validates: Requirements 18.4
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate customers with different spending amounts
    customer_spending=st.lists(
        st.decimals(min_value=Decimal('10.00'), max_value=Decimal('1000.00'), places=2),
        min_size=2,
        max_size=15
    ),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_customer_analytics_top_customers_ranking(client, db_session, customer_spending, seed):
    """
    Property: For any customer analytics report, top customers SHALL be ranked 
    in descending order by total spending.
    
    This property verifies that:
    1. Top customers are correctly ranked by total spending
    2. The ranking is in descending order (highest spending first)
    3. The spending amounts are accurate
    """
    # Create test data
    category = create_test_category(db_session, seed)
    created_customers = []
    created_orders = []
    today = date.today()
    
    for i, spending in enumerate(customer_spending):
        customer = create_test_customer(db_session, seed + i)
        created_customers.append(customer)
        
        # Create one order for this customer with the specified spending
        order = Order(
            order_number=f"ORD-{seed}-{i}",
            source=OrderSource.CUSTOM,
            status=OrderStatus.PENDING,
            customer_id=customer.id,
            order_date=datetime.combine(today, datetime.min.time()),
            subtotal=spending,
            total_amount=spending,
            paid_amount=Decimal('0'),
            balance=spending,
            is_fully_paid=False
        )
        db_session.add(order)
        created_orders.append(order)
    
    db_session.commit()
    
    # Sort spending in descending order to get expected ranking
    expected_ranking = sorted(customer_spending, reverse=True)
    
    # Request customer analytics report for today
    report_request = {
        "date_range": "today"
    }
    
    response = client.post("/api/reports/customer-analytics", json=report_request)
    
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text}"
    
    report = response.json()
    
    # Verify the top customers are ranked in descending order by spending
    top_customers = report["top_customers"]
    
    # Check that spending amounts are in descending order
    for i in range(len(top_customers) - 1):
        current_spending = Decimal(str(top_customers[i]["total_spending"]))
        next_spending = Decimal(str(top_customers[i + 1]["total_spending"]))
        
        assert current_spending >= next_spending, \
            f"Top customers not properly ranked: customer at position {i} has spending {current_spending}, " \
            f"but customer at position {i+1} has higher spending {next_spending}"
    
    # Verify the top customer has the highest spending
    if top_customers:
        top_customer_spending = Decimal(str(top_customers[0]["total_spending"]))
        max_expected_spending = max(expected_ranking)
        
        assert top_customer_spending == max_expected_spending, \
            f"Top customer spending {top_customer_spending} does not match expected maximum {max_expected_spending}"
    
    # Clean up
    for order in created_orders:
        db_session.delete(order)
    for customer in created_customers:
        db_session.delete(customer)
    db_session.delete(category)
    db_session.commit()

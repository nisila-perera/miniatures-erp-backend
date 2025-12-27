"""Property-based tests for best-selling products reporting"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.order import Order, OrderItem
from app.models.customer import Customer
from app.models.product import Product, ProductCategory
from app.models.enums import OrderSource, OrderStatus, ProductSource, CustomerSource


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


def create_test_product(db_session, category_id, seed: int) -> Product:
    """Helper to create a test product"""
    product = Product(
        name=f"Test Product {seed}",
        description=f"Test product description {seed}",
        category_id=category_id,
        base_price=Decimal('50.00'),
        is_colored=False,
        source=ProductSource.ERP,
        is_active=True
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


# Feature: miniatures-erp, Property 54: Best-selling products ranking
# Validates: Requirements 17.1
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate a list of quantities for different products
    quantities=st.lists(
        st.integers(min_value=1, max_value=100),
        min_size=2,
        max_size=10
    ),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_best_selling_products_ranking(client, db_session, quantities, seed):
    """
    Property: For any best-selling products report, products SHALL be ranked 
    in descending order by total quantity sold.
    
    This property verifies that:
    1. Products are correctly ranked by quantity sold
    2. The ranking is in descending order (highest first)
    3. The ranking is accurate for any set of quantities
    """
    # Create test data
    customer = create_test_customer(db_session, seed)
    category = create_test_category(db_session, seed)
    
    # Create products and orders with the generated quantities
    today = date.today()
    created_orders = []
    created_products = []
    
    for i, quantity in enumerate(quantities):
        # Create a product
        product = create_test_product(db_session, category.id, seed * 1000 + i)
        created_products.append(product)
        
        # Create an order with this product
        order = Order(
            order_number=f"ORD-{seed}-{i}",
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
        db_session.flush()
        
        # Create order item with the specified quantity
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_category_id=category.id,
            is_colored=False,
            quantity=quantity,
            unit_price=Decimal('10.00'),
            total_price=Decimal(str(quantity * 10))
        )
        db_session.add(order_item)
        created_orders.append(order)
    
    db_session.commit()
    
    # Sort quantities in descending order to get expected ranking
    expected_ranking = sorted(quantities, reverse=True)
    
    # Request best-sellers report for today
    report_request = {
        "date_range": "today"
    }
    
    response = client.post("/api/reports/best-sellers", json=report_request)
    
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text}"
    
    report = response.json()
    
    # Verify products are ranked in descending order by quantity
    actual_quantities = [product["quantity_sold"] for product in report["products"]]
    
    assert actual_quantities == expected_ranking, \
        f"Products not ranked correctly. Expected {expected_ranking}, got {actual_quantities}"
    
    # Verify the ranking is in descending order
    for i in range(len(actual_quantities) - 1):
        assert actual_quantities[i] >= actual_quantities[i + 1], \
            f"Products not in descending order at position {i}: {actual_quantities[i]} < {actual_quantities[i + 1]}"
    
    # Clean up
    for order in created_orders:
        db_session.delete(order)
    for product in created_products:
        db_session.delete(product)
    db_session.delete(category)
    db_session.delete(customer)
    db_session.commit()


# Feature: miniatures-erp, Property 55: Best-selling products revenue calculation
# Validates: Requirements 17.2
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate product data with quantities and prices
    product_data=st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=50),  # quantity
            st.decimals(min_value=Decimal('1.00'), max_value=Decimal('100.00'), places=2)  # unit price
        ),
        min_size=1,
        max_size=10
    ),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_best_selling_products_revenue_calculation(client, db_session, product_data, seed):
    """
    Property: For any best-selling products report, the revenue per product SHALL equal 
    the sum of all order item totals for that product.
    
    This property verifies that:
    1. Revenue is calculated correctly for each product
    2. All order items for a product are included
    3. The calculation is accurate for any combination of quantities and prices
    """
    # Create test data
    customer = create_test_customer(db_session, seed)
    category = create_test_category(db_session, seed)
    
    # Create products and orders with the generated data
    today = date.today()
    created_orders = []
    created_products = []
    expected_revenues = {}
    
    for i, (quantity, unit_price) in enumerate(product_data):
        # Create a product
        product = create_test_product(db_session, category.id, seed * 1000 + i)
        created_products.append(product)
        
        # Calculate expected revenue for this product
        total_price = Decimal(str(quantity)) * unit_price
        expected_revenues[product.name] = total_price
        
        # Create an order with this product
        order = Order(
            order_number=f"ORD-{seed}-{i}",
            source=OrderSource.CUSTOM,
            status=OrderStatus.PENDING,
            customer_id=customer.id,
            order_date=datetime.combine(today, datetime.min.time()),
            subtotal=total_price,
            total_amount=total_price,
            paid_amount=Decimal('0'),
            balance=total_price,
            is_fully_paid=False
        )
        db_session.add(order)
        db_session.flush()
        
        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_category_id=category.id,
            is_colored=False,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price
        )
        db_session.add(order_item)
        created_orders.append(order)
    
    db_session.commit()
    
    # Request best-sellers report for today
    report_request = {
        "date_range": "today"
    }
    
    response = client.post("/api/reports/best-sellers", json=report_request)
    
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text}"
    
    report = response.json()
    
    # Verify revenue for each product
    for product in report["products"]:
        product_name = product["product_name"]
        actual_revenue = Decimal(str(product["revenue"]))
        expected_revenue = expected_revenues[product_name]
        
        assert actual_revenue == expected_revenue, \
            f"Revenue for product '{product_name}' is {actual_revenue}, expected {expected_revenue}"
    
    # Clean up
    for order in created_orders:
        db_session.delete(order)
    for product in created_products:
        db_session.delete(product)
    db_session.delete(category)
    db_session.delete(customer)
    db_session.commit()

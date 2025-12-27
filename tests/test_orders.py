"""Tests for order management"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from datetime import datetime, date
from decimal import Decimal
from app.main import app
from app.core.database import get_db
from app.models.order import Order, OrderPainter
from app.models.customer import Customer
from app.models.painter import Painter
from app.models.product import ProductCategory
from app.models.enums import OrderSource, OrderStatus


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
    customer_id = customer.id
    yield customer
    # Cleanup
    try:
        db_session.rollback()  # Rollback any pending transaction
        db_session.query(Customer).filter(Customer.id == customer_id).delete()
        db_session.commit()
    except:
        db_session.rollback()


@pytest.fixture
def test_category(db_session):
    """Create a test product category for order items"""
    category = ProductCategory(
        name="Test Category",
        description="Test category for orders"
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    category_id = category.id
    yield category
    # Cleanup
    try:
        db_session.rollback()  # Rollback any pending transaction
        db_session.query(ProductCategory).filter(ProductCategory.id == category_id).delete()
        db_session.commit()
    except:
        db_session.rollback()


@pytest.fixture
def test_painter(db_session):
    """Create a test painter for painter assignments"""
    painter = Painter(
        name="Test Painter",
        email="painter@example.com",
        phone="9876543210",
        is_active=True
    )
    db_session.add(painter)
    db_session.commit()
    db_session.refresh(painter)
    painter_id = painter.id
    yield painter
    # Cleanup
    try:
        db_session.rollback()  # Rollback any pending transaction
        db_session.query(Painter).filter(Painter.id == painter_id).delete()
        db_session.commit()
    except:
        db_session.rollback()


# Feature: miniatures-erp, Property 1: Order source assignment
# Validates: Requirements 1.1
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random order source
    source=st.sampled_from([OrderSource.WEBSITE, OrderSource.CUSTOM, OrderSource.OTHER]),
    order_suffix=st.integers(min_value=1000000, max_value=9999999)
)
def test_order_source_assignment(client, db_session, test_customer, test_category, source, order_suffix):
    """
    Property: For any order created in the system, the order SHALL have a valid source category 
    (website, custom, or other) assigned.
    
    This property verifies that:
    1. Orders can be created with any valid source category
    2. The source is correctly stored in the database
    3. The source is correctly returned when retrieving the order
    4. The source value matches one of the valid enum values
    """
    created_order = None
    
    try:
        # Create an order with the specified source
        import time
        unique_suffix = f"{order_suffix}-{int(time.time() * 1000000)}"
        order_data = {
            "order_number": f"ORD-{unique_suffix}",
            "source": source.value,
            "customer_id": str(test_customer.id),
            "order_date": datetime.utcnow().isoformat(),
            "items": [
                {
                    "product_name": "Test Product",
                    "product_category_id": str(test_category.id),
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        }
        
        # Create order via API
        response = client.post("/api/orders", json=order_data)
        
        # Verify order was created successfully
        assert response.status_code == 201, \
            f"Expected status 201, got {response.status_code}: {response.text}"
        
        order_response = response.json()
        created_order_id = order_response["id"]
        
        # Verify the source is assigned and matches the input
        assert "source" in order_response, \
            "Order response should contain 'source' field"
        
        assert order_response["source"] == source.value, \
            f"Expected source '{source.value}', got '{order_response['source']}'"
        
        # Verify the source is one of the valid values
        valid_sources = [OrderSource.WEBSITE.value, OrderSource.CUSTOM.value, OrderSource.OTHER.value]
        assert order_response["source"] in valid_sources, \
            f"Source '{order_response['source']}' is not a valid source category"
        
        # Retrieve the order and verify source persists
        get_response = client.get(f"/api/orders/{created_order_id}")
        assert get_response.status_code == 200
        
        retrieved_order = get_response.json()
        assert retrieved_order["source"] == source.value, \
            f"Retrieved order source '{retrieved_order['source']}' does not match created source '{source.value}'"
        
        # Verify in database
        db_order = db_session.query(Order).filter(Order.id == created_order_id).first()
        assert db_order is not None, \
            f"Order {created_order_id} should exist in database"
        
        assert db_order.source == source, \
            f"Database order source '{db_order.source}' does not match expected '{source}'"
        
        created_order = db_order
    
    finally:
        # Clean up: delete the created order
        try:
            if created_order and created_order.id:
                db_session.rollback()  # Rollback any pending transaction
                db_session.query(Order).filter(Order.id == created_order.id).delete()
                db_session.commit()
        except:
            db_session.rollback()




# Feature: miniatures-erp, Property 2: Order filtering by source
# Validates: Requirements 1.3
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random orders with different sources
    order_count=st.integers(min_value=2, max_value=8),
    filter_source=st.sampled_from([OrderSource.WEBSITE, OrderSource.CUSTOM, OrderSource.OTHER])
)
def test_order_filtering_by_source(client, db_session, test_customer, test_category, order_count, filter_source):
    """
    Property: For any set of orders and any source category filter, all returned orders 
    SHALL have the specified source category.
    
    This property verifies that:
    1. Orders can be filtered by source
    2. All returned orders match the filter criteria
    3. Orders with different sources are excluded from results
    4. The filtering is accurate and complete
    """
    created_orders = []
    
    try:
        # Create orders with different sources
        sources = [OrderSource.WEBSITE, OrderSource.CUSTOM, OrderSource.OTHER]
        import time
        base_time = int(time.time() * 1000000)
        
        for i in range(order_count):
            source = sources[i % len(sources)]
            order_data = {
                "order_number": f"ORD-FILTER-{base_time}-{i}",
                "source": source.value,
                "customer_id": str(test_customer.id),
                "order_date": datetime.utcnow().isoformat(),
                "items": [
                    {
                        "product_name": f"Test Product {i}",
                        "product_category_id": str(test_category.id),
                        "quantity": 1,
                        "unit_price": 100.00
                    }
                ]
            }
            
            response = client.post("/api/orders", json=order_data)
            assert response.status_code == 201
            created_orders.append(response.json()["id"])
        
        # Filter orders by the specified source
        response = client.get(f"/api/orders?source={filter_source.value}")
        
        assert response.status_code == 200
        filtered_orders = response.json()
        
        # Verify all returned orders have the specified source
        for order in filtered_orders:
            if order["id"] in created_orders:
                assert order["source"] == filter_source.value, \
                    f"Order {order['id']} has source '{order['source']}' but filter was '{filter_source.value}'"
        
        # Verify that orders with the filter source are included
        our_filtered_orders = [o for o in filtered_orders if o["id"] in created_orders]
        expected_count = sum(1 for i in range(order_count) if sources[i % len(sources)] == filter_source)
        
        assert len(our_filtered_orders) == expected_count, \
            f"Expected {expected_count} orders with source '{filter_source.value}', got {len(our_filtered_orders)}"
    
    finally:
        # Clean up: delete all created orders
        try:
            for order_id in created_orders:
                db_session.rollback()
                db_session.query(Order).filter(Order.id == order_id).delete()
            db_session.commit()
        except:
            db_session.rollback()


# Feature: miniatures-erp, Property 19: New order default status
# Validates: Requirements 6.1
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random order data
    source=st.sampled_from([OrderSource.WEBSITE, OrderSource.CUSTOM, OrderSource.OTHER]),
    order_suffix=st.integers(min_value=1000000, max_value=9999999)
)
def test_new_order_default_status(client, db_session, test_customer, test_category, source, order_suffix):
    """
    Property: For any newly created order, the initial status SHALL be "Pending".
    
    This property verifies that:
    1. All new orders start with PENDING status
    2. The status is set automatically without explicit specification
    3. The default status is consistent across all order sources
    4. The status is correctly stored and retrieved
    """
    created_order = None
    
    try:
        import time
        unique_suffix = f"{order_suffix}-{int(time.time() * 1000000)}"
        
        # Create an order without specifying status
        order_data = {
            "order_number": f"ORD-STATUS-{unique_suffix}",
            "source": source.value,
            "customer_id": str(test_customer.id),
            "order_date": datetime.utcnow().isoformat(),
            "items": [
                {
                    "product_name": "Test Product",
                    "product_category_id": str(test_category.id),
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        }
        
        response = client.post("/api/orders", json=order_data)
        
        assert response.status_code == 201
        order_response = response.json()
        created_order_id = order_response["id"]
        
        # Verify the status is PENDING
        assert order_response["status"] == OrderStatus.PENDING.value, \
            f"Expected new order status to be '{OrderStatus.PENDING.value}', got '{order_response['status']}'"
        
        # Retrieve the order and verify status persists
        get_response = client.get(f"/api/orders/{created_order_id}")
        assert get_response.status_code == 200
        
        retrieved_order = get_response.json()
        assert retrieved_order["status"] == OrderStatus.PENDING.value, \
            f"Retrieved order status should be '{OrderStatus.PENDING.value}', got '{retrieved_order['status']}'"
        
        # Verify in database
        db_order = db_session.query(Order).filter(Order.id == created_order_id).first()
        assert db_order is not None
        assert db_order.status == OrderStatus.PENDING, \
            f"Database order status should be '{OrderStatus.PENDING}', got '{db_order.status}'"
        
        created_order = db_order
    
    finally:
        # Clean up
        try:
            if created_order and created_order.id:
                db_session.rollback()
                db_session.query(Order).filter(Order.id == created_order.id).delete()
                db_session.commit()
        except:
            db_session.rollback()


# Feature: miniatures-erp, Property 20: Order status validation
# Validates: Requirements 6.2
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random valid status
    new_status=st.sampled_from([
        OrderStatus.PENDING, OrderStatus.PRINTING, OrderStatus.IN_PRODUCTION,
        OrderStatus.PAINTING, OrderStatus.FINAL_CHECKS, OrderStatus.SHIPPED,
        OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.RETURNED
    ]),
    order_suffix=st.integers(min_value=1000000, max_value=9999999)
)
def test_order_status_validation(client, db_session, test_customer, test_category, new_status, order_suffix):
    """
    Property: For any order status update, the system SHALL accept only valid status values.
    
    This property verifies that:
    1. All valid status values are accepted
    2. Status updates are correctly stored
    3. Status updates are correctly retrieved
    4. The system enforces the status enum
    """
    created_order = None
    
    try:
        import time
        unique_suffix = f"{order_suffix}-{int(time.time() * 1000000)}"
        
        # Create an order
        order_data = {
            "order_number": f"ORD-VALID-{unique_suffix}",
            "source": OrderSource.CUSTOM.value,
            "customer_id": str(test_customer.id),
            "order_date": datetime.utcnow().isoformat(),
            "items": [
                {
                    "product_name": "Test Product",
                    "product_category_id": str(test_category.id),
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        }
        
        response = client.post("/api/orders", json=order_data)
        assert response.status_code == 201
        created_order_id = response.json()["id"]
        
        # Update the order status to a valid value
        update_response = client.put(
            f"/api/orders/{created_order_id}",
            json={"status": new_status.value}
        )
        
        assert update_response.status_code == 200, \
            f"Expected status 200 for valid status '{new_status.value}', got {update_response.status_code}"
        
        updated_order = update_response.json()
        assert updated_order["status"] == new_status.value, \
            f"Expected status '{new_status.value}', got '{updated_order['status']}'"
        
        # Verify in database
        db_order = db_session.query(Order).filter(Order.id == created_order_id).first()
        assert db_order is not None
        assert db_order.status == new_status, \
            f"Database order status should be '{new_status}', got '{db_order.status}'"
        
        created_order = db_order
    
    finally:
        # Clean up
        try:
            if created_order and created_order.id:
                db_session.rollback()
                db_session.query(Order).filter(Order.id == created_order.id).delete()
                db_session.commit()
        except:
            db_session.rollback()


# Feature: miniatures-erp, Property 21: Order filtering by status
# Validates: Requirements 6.4
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random orders with different statuses
    order_count=st.integers(min_value=2, max_value=8),
    filter_status=st.sampled_from([
        OrderStatus.PENDING, OrderStatus.PRINTING, OrderStatus.IN_PRODUCTION,
        OrderStatus.PAINTING, OrderStatus.SHIPPED
    ])
)
def test_order_filtering_by_status(client, db_session, test_customer, test_category, order_count, filter_status):
    """
    Property: For any set of orders and any status filter, all returned orders 
    SHALL have the specified status.
    
    This property verifies that:
    1. Orders can be filtered by status
    2. All returned orders match the filter criteria
    3. Orders with different statuses are excluded from results
    4. The filtering is accurate and complete
    """
    created_orders = []
    
    try:
        # Create orders with different statuses
        statuses = [OrderStatus.PENDING, OrderStatus.PRINTING, OrderStatus.IN_PRODUCTION, 
                   OrderStatus.PAINTING, OrderStatus.SHIPPED]
        import time
        base_time = int(time.time() * 1000000)
        
        for i in range(order_count):
            status = statuses[i % len(statuses)]
            order_data = {
                "order_number": f"ORD-STAT-{base_time}-{i}",
                "source": OrderSource.CUSTOM.value,
                "customer_id": str(test_customer.id),
                "order_date": datetime.utcnow().isoformat(),
                "items": [
                    {
                        "product_name": f"Test Product {i}",
                        "product_category_id": str(test_category.id),
                        "quantity": 1,
                        "unit_price": 100.00
                    }
                ]
            }
            
            response = client.post("/api/orders", json=order_data)
            assert response.status_code == 201
            order_id = response.json()["id"]
            created_orders.append(order_id)
            
            # Update status if not PENDING
            if status != OrderStatus.PENDING:
                client.put(f"/api/orders/{order_id}", json={"status": status.value})
        
        # Filter orders by the specified status
        response = client.get(f"/api/orders?status={filter_status.value}")
        
        assert response.status_code == 200
        filtered_orders = response.json()
        
        # Verify all returned orders have the specified status
        for order in filtered_orders:
            if order["id"] in created_orders:
                assert order["status"] == filter_status.value, \
                    f"Order {order['id']} has status '{order['status']}' but filter was '{filter_status.value}'"
        
        # Verify that orders with the filter status are included
        our_filtered_orders = [o for o in filtered_orders if o["id"] in created_orders]
        expected_count = sum(1 for i in range(order_count) if statuses[i % len(statuses)] == filter_status)
        
        assert len(our_filtered_orders) == expected_count, \
            f"Expected {expected_count} orders with status '{filter_status.value}', got {len(our_filtered_orders)}"
    
    finally:
        # Clean up: delete all created orders
        try:
            for order_id in created_orders:
                db_session.rollback()
                db_session.query(Order).filter(Order.id == order_id).delete()
            db_session.commit()
        except:
            db_session.rollback()


# Feature: miniatures-erp, Property 23: Painter assignment persistence
# Validates: Requirements 7.1
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random painter assignment data
    painting_cost=st.decimals(min_value=10, max_value=1000, places=2),
    order_suffix=st.integers(min_value=1000000, max_value=9999999)
)
def test_painter_assignment_persistence(client, db_session, test_customer, test_category, test_painter, painting_cost, order_suffix):
    """
    Property: For any painter assigned to an order, retrieving the order SHALL show the painter assignment.
    
    This property verifies that:
    1. Painters can be assigned to orders
    2. Painter assignments are correctly stored
    3. Painter assignments are correctly retrieved
    4. Assignment data persists accurately
    """
    created_order = None
    
    try:
        import time
        unique_suffix = f"{order_suffix}-{int(time.time() * 1000000)}"
        
        # Create an order
        order_data = {
            "order_number": f"ORD-PAINT-{unique_suffix}",
            "source": OrderSource.CUSTOM.value,
            "customer_id": str(test_customer.id),
            "order_date": datetime.utcnow().isoformat(),
            "items": [
                {
                    "product_name": "Test Product",
                    "product_category_id": str(test_category.id),
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        }
        
        response = client.post("/api/orders", json=order_data)
        assert response.status_code == 201
        created_order_id = response.json()["id"]
        
        # Assign a painter to the order
        painter_data = {
            "painter_id": str(test_painter.id),
            "assigned_date": date.today().isoformat(),
            "painting_cost": float(painting_cost)
        }
        
        assign_response = client.post(
            f"/api/orders/{created_order_id}/painters",
            json=painter_data
        )
        
        assert assign_response.status_code == 201, \
            f"Expected status 201 for painter assignment, got {assign_response.status_code}"
        
        assignment = assign_response.json()
        assert assignment["painter_id"] == str(test_painter.id)
        assert assignment["order_id"] == created_order_id
        
        # Retrieve painter assignments for the order
        get_response = client.get(f"/api/orders/{created_order_id}/painters")
        assert get_response.status_code == 200
        
        painters = get_response.json()
        assert len(painters) >= 1, \
            "Order should have at least one painter assignment"
        
        # Verify the painter assignment is present
        matching_painters = [p for p in painters if p["painter_id"] == str(test_painter.id)]
        assert len(matching_painters) == 1, \
            f"Expected exactly 1 painter assignment for painter {test_painter.id}, found {len(matching_painters)}"
        
        # Verify in database
        db_order = db_session.query(Order).filter(Order.id == created_order_id).first()
        assert db_order is not None
        assert len(db_order.painters) >= 1, \
            "Order should have at least one painter in database"
        
        created_order = db_order
    
    finally:
        # Clean up
        try:
            if created_order and created_order.id:
                db_session.rollback()
                db_session.query(Order).filter(Order.id == created_order.id).delete()
                db_session.commit()
        except:
            db_session.rollback()


# Feature: miniatures-erp, Property 24: Multiple painter assignments
# Validates: Requirements 7.2
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random number of painters to assign
    painter_count=st.integers(min_value=2, max_value=5),
    order_suffix=st.integers(min_value=1000000, max_value=9999999)
)
def test_multiple_painter_assignments(client, db_session, test_customer, test_category, painter_count, order_suffix):
    """
    Property: For any order with multiple painters assigned, retrieving the order 
    SHALL show all painter assignments.
    
    This property verifies that:
    1. Multiple painters can be assigned to a single order
    2. All painter assignments are correctly stored
    3. All painter assignments are correctly retrieved
    4. No painter assignments are lost
    """
    created_order = None
    created_painters = []
    
    try:
        import time
        unique_suffix = f"{order_suffix}-{int(time.time() * 1000000)}"
        
        # Create an order
        order_data = {
            "order_number": f"ORD-MULTI-{unique_suffix}",
            "source": OrderSource.CUSTOM.value,
            "customer_id": str(test_customer.id),
            "order_date": datetime.utcnow().isoformat(),
            "items": [
                {
                    "product_name": "Test Product",
                    "product_category_id": str(test_category.id),
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        }
        
        response = client.post("/api/orders", json=order_data)
        assert response.status_code == 201
        created_order_id = response.json()["id"]
        
        # Create and assign multiple painters
        painter_ids = []
        for i in range(painter_count):
            painter = Painter(
                name=f"Painter {unique_suffix}-{i}",
                email=f"painter{unique_suffix}{i}@example.com",
                phone=f"123456{i}",
                is_active=True
            )
            db_session.add(painter)
            db_session.commit()
            db_session.refresh(painter)
            created_painters.append(painter)
            painter_ids.append(str(painter.id))
            
            # Assign painter to order
            painter_data = {
                "painter_id": str(painter.id),
                "assigned_date": date.today().isoformat(),
                "painting_cost": 100.00 + (i * 10)
            }
            
            assign_response = client.post(
                f"/api/orders/{created_order_id}/painters",
                json=painter_data
            )
            
            assert assign_response.status_code == 201
        
        # Retrieve all painter assignments for the order
        get_response = client.get(f"/api/orders/{created_order_id}/painters")
        assert get_response.status_code == 200
        
        painters = get_response.json()
        
        # Verify all painters are present
        retrieved_painter_ids = {p["painter_id"] for p in painters}
        for painter_id in painter_ids:
            assert painter_id in retrieved_painter_ids, \
                f"Painter {painter_id} should be in the list of assigned painters"
        
        # Verify the count matches
        our_painters = [p for p in painters if p["painter_id"] in painter_ids]
        assert len(our_painters) == painter_count, \
            f"Expected {painter_count} painter assignments, found {len(our_painters)}"
        
        # Verify in database
        db_order = db_session.query(Order).filter(Order.id == created_order_id).first()
        assert db_order is not None
        assert len(db_order.painters) == painter_count, \
            f"Order should have {painter_count} painters in database, found {len(db_order.painters)}"
        
        created_order = db_order
    
    finally:
        # Clean up
        try:
            if created_order and created_order.id:
                db_session.rollback()
                db_session.query(Order).filter(Order.id == created_order.id).delete()
                db_session.commit()
            
            for painter in created_painters:
                db_session.rollback()
                db_session.query(Painter).filter(Painter.id == painter.id).delete()
            db_session.commit()
        except:
            db_session.rollback()


# Feature: miniatures-erp, Property 25: Painter assignment date recording
# Validates: Requirements 7.3
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random assignment date
    days_offset=st.integers(min_value=-30, max_value=30),
    order_suffix=st.integers(min_value=1000000, max_value=9999999)
)
def test_painter_assignment_date_recording(client, db_session, test_customer, test_category, test_painter, days_offset, order_suffix):
    """
    Property: For any painter assignment, the assignment SHALL have a recorded date.
    
    This property verifies that:
    1. Painter assignments include a date
    2. The assignment date is correctly stored
    3. The assignment date is correctly retrieved
    4. The date persists accurately
    """
    created_order = None
    
    try:
        import time
        from datetime import timedelta
        unique_suffix = f"{order_suffix}-{int(time.time() * 1000000)}"
        
        # Create an order
        order_data = {
            "order_number": f"ORD-DATE-{unique_suffix}",
            "source": OrderSource.CUSTOM.value,
            "customer_id": str(test_customer.id),
            "order_date": datetime.utcnow().isoformat(),
            "items": [
                {
                    "product_name": "Test Product",
                    "product_category_id": str(test_category.id),
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        }
        
        response = client.post("/api/orders", json=order_data)
        assert response.status_code == 201
        created_order_id = response.json()["id"]
        
        # Calculate assignment date
        assignment_date = date.today() + timedelta(days=days_offset)
        
        # Assign a painter with a specific date
        painter_data = {
            "painter_id": str(test_painter.id),
            "assigned_date": assignment_date.isoformat(),
            "painting_cost": 150.00
        }
        
        assign_response = client.post(
            f"/api/orders/{created_order_id}/painters",
            json=painter_data
        )
        
        assert assign_response.status_code == 201
        assignment = assign_response.json()
        
        # Verify the assignment has a date
        assert "assigned_date" in assignment, \
            "Painter assignment should have an assigned_date field"
        
        assert assignment["assigned_date"] is not None, \
            "Painter assignment date should not be None"
        
        assert assignment["assigned_date"] == assignment_date.isoformat(), \
            f"Expected assignment date '{assignment_date.isoformat()}', got '{assignment['assigned_date']}'"
        
        # Retrieve and verify
        get_response = client.get(f"/api/orders/{created_order_id}/painters")
        assert get_response.status_code == 200
        
        painters = get_response.json()
        matching_painters = [p for p in painters if p["painter_id"] == str(test_painter.id)]
        assert len(matching_painters) == 1
        
        assert matching_painters[0]["assigned_date"] == assignment_date.isoformat(), \
            f"Retrieved assignment date should be '{assignment_date.isoformat()}'"
        
        # Verify in database
        db_order = db_session.query(Order).filter(Order.id == created_order_id).first()
        assert db_order is not None
        assert len(db_order.painters) >= 1
        
        db_assignment = db_order.painters[0]
        assert db_assignment.assigned_date == assignment_date, \
            f"Database assignment date should be '{assignment_date}', got '{db_assignment.assigned_date}'"
        
        created_order = db_order
    
    finally:
        # Clean up
        try:
            if created_order and created_order.id:
                db_session.rollback()
                db_session.query(Order).filter(Order.id == created_order.id).delete()
                db_session.commit()
        except:
            db_session.rollback()

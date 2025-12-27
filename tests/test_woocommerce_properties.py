"""Property-based tests for WooCommerce integration"""
import pytest
from unittest.mock import Mock, patch
from app.services.woocommerce_integration import WooCommerceIntegrationService
from app.models.enums import CustomerSource, ProductSource, OrderSource
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order


@patch('app.services.woocommerce_integration.WooCommerceClient')
def test_imported_customer_source_flagging(mock_client_class, db_session):
    """
    Feature: miniatures-erp, Property 3: Imported customer source flagging
    
    For any customer imported from WooCommerce, the customer SHALL have 
    source flag set to "woocommerce".
    
    Validates: Requirements 2.5
    """
    # Mock WooCommerce customer data
    wc_customers = [
        {
            "id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "billing": {
                "phone": "1234567890",
                "address_1": "123 Main St",
                "city": "Test City",
                "postcode": "12345"
            }
        }
    ]
    
    # Configure the mock - return customers on first call, empty list on second to break pagination
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    mock_client.get_customers.side_effect = [wc_customers, []]
    
    # Create service and sync customers
    service = WooCommerceIntegrationService(db_session)
    created, updated = service.sync_customers()
    
    # Verify customer was created
    assert created == 1
    assert updated == 0
    
    # Verify customer has WOOCOMMERCE source
    customer = db_session.query(Customer).filter(
        Customer.woocommerce_id == 12345
    ).first()
    
    assert customer is not None
    assert customer.source == CustomerSource.WOOCOMMERCE


@patch('app.services.woocommerce_integration.WooCommerceClient')
def test_imported_product_source_flagging(mock_client_class, db_session):
    """
    Feature: miniatures-erp, Property 4: Imported product source flagging
    
    For any product imported from WooCommerce, the product SHALL have 
    source flag set to "woocommerce".
    
    Validates: Requirements 2.6
    """
    # Mock WooCommerce product data
    wc_products = [
        {
            "id": 54321,
            "name": "Test Product",
            "description": "Test Description",
            "price": "99.99",
            "status": "publish"
        }
    ]
    
    # Configure the mock - return products on first call, empty list on second to break pagination
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    mock_client.get_products.side_effect = [wc_products, []]
    
    # Create service and sync products
    service = WooCommerceIntegrationService(db_session)
    created, updated = service.sync_products()
    
    # Verify product was created
    assert created == 1
    assert updated == 0
    
    # Verify product has WOOCOMMERCE source
    product = db_session.query(Product).filter(
        Product.woocommerce_id == 54321
    ).first()
    
    assert product is not None
    assert product.source == ProductSource.WOOCOMMERCE


@patch('app.services.woocommerce_integration.WooCommerceClient')
def test_import_idempotency(mock_client_class, db_session):
    """
    Feature: miniatures-erp, Property 6: Import idempotency
    
    For any data imported from WooCommerce, importing the same data again 
    SHALL update existing records rather than create duplicates.
    
    Validates: Requirements 2.8
    """
    from app.models.product import ProductCategory
    
    # Mock WooCommerce customer data
    wc_customers = [
        {
            "id": 99999,
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "billing": {
                "phone": "9876543210",
                "address_1": "456 Oak Ave",
                "city": "Another City",
                "postcode": "54321"
            }
        }
    ]
    
    # Mock WooCommerce product data
    wc_products = [
        {
            "id": 77777,
            "name": "Idempotent Product",
            "description": "Test product for idempotency",
            "price": "49.99",
            "status": "publish"
        }
    ]
    
    # Mock WooCommerce order data
    wc_orders = [
        {
            "id": 66666,
            "customer_id": 99999,
            "status": "processing",
            "date_created": "2024-01-15T10:30:00Z",
            "total": "149.99",
            "customer_note": "Test order",
            "billing": {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@example.com",
                "phone": "9876543210",
                "address_1": "456 Oak Ave",
                "city": "Another City",
                "postcode": "54321"
            },
            "line_items": [
                {
                    "product_id": 77777,
                    "name": "Idempotent Product",
                    "quantity": 3,
                    "price": "49.99",
                    "total": "149.97"
                }
            ]
        }
    ]
    
    # Configure the mock
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    
    # Setup mock responses for first sync cycle
    mock_client.get_customers.side_effect = [wc_customers, []]
    mock_client.get_products.side_effect = [wc_products, []]
    mock_client.get_orders.side_effect = [wc_orders, []]
    
    # Create service and perform first sync
    service = WooCommerceIntegrationService(db_session)
    
    # Sync customers first time
    cust_created1, cust_updated1 = service.sync_customers()
    assert cust_created1 == 1
    assert cust_updated1 == 0
    
    # Sync products first time
    prod_created1, prod_updated1 = service.sync_products()
    assert prod_created1 == 1
    assert prod_updated1 == 0
    
    # Sync orders first time
    order_created1, order_updated1 = service.sync_orders()
    assert order_created1 == 1
    assert order_updated1 == 0
    
    # Count records after first sync
    customer_count_first = db_session.query(Customer).filter(
        Customer.woocommerce_id == 99999
    ).count()
    
    product_count_first = db_session.query(Product).filter(
        Product.woocommerce_id == 77777
    ).count()
    
    order_count_first = db_session.query(Order).filter(
        Order.woocommerce_id == 66666
    ).count()
    
    # Reset mock for second sync cycle
    mock_client.get_customers.side_effect = [wc_customers, []]
    mock_client.get_products.side_effect = [wc_products, []]
    mock_client.get_orders.side_effect = [wc_orders, []]
    
    # Sync again with the same data
    cust_created2, cust_updated2 = service.sync_customers()
    prod_created2, prod_updated2 = service.sync_products()
    order_created2, order_updated2 = service.sync_orders()
    
    # Count records after second sync
    customer_count_second = db_session.query(Customer).filter(
        Customer.woocommerce_id == 99999
    ).count()
    
    product_count_second = db_session.query(Product).filter(
        Product.woocommerce_id == 77777
    ).count()
    
    order_count_second = db_session.query(Order).filter(
        Order.woocommerce_id == 66666
    ).count()
    
    # Verify no duplicates were created for any entity type
    assert customer_count_first == customer_count_second == 1
    assert product_count_first == product_count_second == 1
    assert order_count_first == order_count_second == 1
    
    # Verify second sync updated existing records instead of creating new ones
    assert cust_created2 == 0 and cust_updated2 == 1
    assert prod_created2 == 0 and prod_updated2 == 1
    assert order_created2 == 0 and order_updated2 == 1


@patch('app.services.woocommerce_integration.WooCommerceClient')
def test_conditional_woocommerce_status_sync(mock_client_class, db_session):
    """
    Feature: miniatures-erp, Property 22: Conditional WooCommerce status sync
    
    For any order status update, the system SHALL sync to WooCommerce 
    only if the order source is "website".
    
    Validates: Requirements 6.5
    """
    from app.repositories.customer import CustomerRepository
    from app.repositories.order import OrderRepository
    from app.schemas.customer import CustomerCreate
    from app.schemas.order import OrderCreate, OrderItemCreate
    from app.models.product import ProductCategory
    
    # Configure the mock
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    
    # Create a customer
    customer_repo = CustomerRepository(db_session)
    customer = customer_repo.create(CustomerCreate(
        name="Test Customer",
        email="test@example.com",
        phone="1234567890",
        address="123 Test St",
        city="Test City",
        postal_code="12345",
        source=CustomerSource.ERP
    ))
    
    # Create a category
    category = ProductCategory(name="Test Category Sync", description="Test")
    db_session.add(category)
    db_session.commit()
    
    # Create a CUSTOM order (not website)
    order_repo = OrderRepository(db_session)
    order = order_repo.create(OrderCreate(
        order_number="TEST-CUSTOM-001",
        source=OrderSource.CUSTOM,
        customer_id=str(customer.id),
        subtotal=100.00,
        total_amount=100.00,
        items=[
            OrderItemCreate(
                product_name="Test Product",
                product_category_id=str(category.id),
                quantity=1,
                unit_price=100.00,
                total_price=100.00,
                is_colored=False
            )
        ]
    ))
    
    # Try to sync status
    service = WooCommerceIntegrationService(db_session)
    result = service.sync_order_status_to_woocommerce(str(order.id))
    
    # Verify sync was NOT performed for non-website orders
    assert result is False
    assert not mock_client.update_order_status.called


@patch('app.services.woocommerce_integration.WooCommerceClient')
def test_order_status_sync_to_woocommerce(mock_client_class, db_session):
    """
    Feature: miniatures-erp, Property 5: Order status sync to WooCommerce
    
    For any website-sourced order, when the order status is updated, 
    the system SHALL sync the status to WooCommerce.
    
    Validates: Requirements 2.7
    """
    from app.repositories.customer import CustomerRepository
    from app.repositories.order import OrderRepository
    from app.schemas.customer import CustomerCreate
    from app.schemas.order import OrderCreate, OrderItemCreate
    from app.models.product import ProductCategory
    
    # Configure the mock
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    mock_client.update_order_status.return_value = {"id": 88888, "status": "processing"}
    
    # Create a customer
    customer_repo = CustomerRepository(db_session)
    customer = customer_repo.create(CustomerCreate(
        name="Test Customer",
        email="test@example.com",
        phone="1234567890",
        address="123 Test St",
        city="Test City",
        postal_code="12345",
        source=CustomerSource.WOOCOMMERCE,
        woocommerce_id=88888
    ))
    
    # Create a category
    category = ProductCategory(name="Test Category Website", description="Test")
    db_session.add(category)
    db_session.commit()
    
    # Create a WEBSITE order
    order_repo = OrderRepository(db_session)
    order = order_repo.create(OrderCreate(
        order_number="WC-88888",
        source=OrderSource.WEBSITE,
        customer_id=str(customer.id),
        subtotal=100.00,
        total_amount=100.00,
        items=[
            OrderItemCreate(
                product_name="Test Product",
                product_category_id=str(category.id),
                quantity=1,
                unit_price=100.00,
                total_price=100.00,
                is_colored=False
            )
        ]
    ))
    
    # Set the woocommerce_id directly on the order (simulating an imported order)
    order.woocommerce_id = 88888
    db_session.commit()
    db_session.refresh(order)
    
    # Sync the status back to WooCommerce
    service = WooCommerceIntegrationService(db_session)
    result = service.sync_order_status_to_woocommerce(str(order.id))
    
    # Verify the sync was attempted
    assert result is True
    assert mock_client.update_order_status.called

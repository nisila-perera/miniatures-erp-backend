"""Basic tests for database models"""
import pytest
from app.models.product import Product, ProductCategory
from app.models.customer import Customer
from app.models.painter import Painter
from app.models.payment import PaymentMethod
from app.models.enums import ProductSource, CustomerSource, CommissionType
from decimal import Decimal


@pytest.mark.unit
def test_product_category_creation(db_session):
    """Test creating a product category"""
    category = ProductCategory(
        name="Test Category",
        description="A test category"
    )
    db_session.add(category)
    db_session.commit()
    
    assert category.id is not None
    assert category.name == "Test Category"
    assert category.created_at is not None


@pytest.mark.unit
def test_product_creation(db_session):
    """Test creating a product"""
    # First create a category
    category = ProductCategory(name="Test Category")
    db_session.add(category)
    db_session.commit()
    
    # Create a product
    product = Product(
        name="Test Product",
        description="A test product",
        category_id=category.id,
        base_price=Decimal("99.99"),
        is_colored=True,
        source=ProductSource.ERP
    )
    db_session.add(product)
    db_session.commit()
    
    assert product.id is not None
    assert product.name == "Test Product"
    assert product.base_price == Decimal("99.99")
    assert product.source == ProductSource.ERP


@pytest.mark.unit
def test_customer_creation(db_session):
    """Test creating a customer"""
    customer = Customer(
        name="John Doe",
        email="john@example.com",
        phone="1234567890",
        source=CustomerSource.ERP
    )
    db_session.add(customer)
    db_session.commit()
    
    assert customer.id is not None
    assert customer.name == "John Doe"
    assert customer.email == "john@example.com"


@pytest.mark.unit
def test_painter_creation(db_session):
    """Test creating a painter"""
    painter = Painter(
        name="Jane Artist",
        email="jane@example.com",
        is_active=True
    )
    db_session.add(painter)
    db_session.commit()
    
    assert painter.id is not None
    assert painter.name == "Jane Artist"
    assert painter.is_active is True


@pytest.mark.unit
def test_payment_method_creation(db_session):
    """Test creating a payment method"""
    payment_method = PaymentMethod(
        name="Credit Card",
        commission_type=CommissionType.PERCENTAGE,
        commission_value=Decimal("2.5"),
        is_active=True
    )
    db_session.add(payment_method)
    db_session.commit()
    
    assert payment_method.id is not None
    assert payment_method.name == "Credit Card"
    assert payment_method.commission_value == Decimal("2.5")

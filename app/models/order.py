"""Order, OrderItem, and OrderPainter models"""
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, Integer, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base, TimestampMixin, generate_uuid
from app.models.enums import OrderSource, OrderStatus, DiscountType


class Order(Base, TimestampMixin):
    """Order model"""
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    order_number = Column(String(50), unique=True, nullable=False)
    source = Column(ENUM(OrderSource, name="order_source"), nullable=False)
    status = Column(ENUM(OrderStatus, name="order_status"), nullable=False, default=OrderStatus.PENDING)
    customer_id = Column(UUID(as_uuid=False), ForeignKey("customers.id"), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    discount_type = Column(ENUM(DiscountType, name="discount_type"))
    discount_reason = Column(String(500))
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    paid_amount = Column(Numeric(10, 2), default=0)
    balance = Column(Numeric(10, 2), default=0)
    is_fully_paid = Column(Boolean, default=False)
    notes = Column(String(2000))
    woocommerce_id = Column(Integer)
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    painters = relationship("OrderPainter", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base, TimestampMixin):
    """Order item model"""
    __tablename__ = "order_items"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    order_id = Column(UUID(as_uuid=False), ForeignKey("orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=False), ForeignKey("products.id"))
    product_name = Column(String(255), nullable=False)
    product_category_id = Column(UUID(as_uuid=False), ForeignKey("product_categories.id"), nullable=False)
    is_colored = Column(Boolean, default=False)
    dimensions = Column(String(255))
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0)
    discount_type = Column(ENUM(DiscountType, name="order_item_discount_type"))
    discount_reason = Column(String(500))
    total_price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(String(500))
    custom_description = Column(String(1000))
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    category = relationship("ProductCategory")


class OrderPainter(Base, TimestampMixin):
    """Order painter assignment model"""
    __tablename__ = "order_painters"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    order_id = Column(UUID(as_uuid=False), ForeignKey("orders.id"), nullable=False)
    painter_id = Column(UUID(as_uuid=False), ForeignKey("painters.id"), nullable=False)
    assigned_date = Column(Date, nullable=False)
    painting_cost = Column(Numeric(10, 2), nullable=False)
    notes = Column(String(1000))
    
    # Relationships
    order = relationship("Order", back_populates="painters")
    painter = relationship("Painter")
    
    @property
    def painter_name(self) -> str:
        """Get the painter's name"""
        return self.painter.name if self.painter else None

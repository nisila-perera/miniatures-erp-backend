"""Payment and PaymentMethod models"""
from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_uuid
from app.models.enums import CommissionType


class PaymentMethod(Base, TimestampMixin):
    """Payment method model"""
    __tablename__ = "payment_methods"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    commission_type = Column(ENUM(CommissionType, name="commission_type"), nullable=False)
    commission_value = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    payments = relationship("Payment", back_populates="payment_method")


class Payment(Base, TimestampMixin):
    """Payment model"""
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    order_id = Column(UUID(as_uuid=False), ForeignKey("orders.id"), nullable=False)
    payment_method_id = Column(UUID(as_uuid=False), ForeignKey("payment_methods.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    commission_amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(Date, nullable=False)
    reference_number = Column(String(255))
    notes = Column(String(1000))
    
    # Relationships
    order = relationship("Order", back_populates="payments")
    payment_method = relationship("PaymentMethod", back_populates="payments")

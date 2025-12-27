"""Customer model"""
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_uuid
from app.models.enums import CustomerSource


class Customer(Base, TimestampMixin):
    """Customer model"""
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    address = Column(String(500))
    city = Column(String(100))
    postal_code = Column(String(20))
    source = Column(ENUM(CustomerSource, name="customer_source"), nullable=False, default=CustomerSource.ERP)
    woocommerce_id = Column(Integer)
    
    # Relationships
    orders = relationship("Order", back_populates="customer")

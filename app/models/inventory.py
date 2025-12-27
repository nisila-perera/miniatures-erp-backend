"""Inventory models - Resin and PaintBottle"""
from sqlalchemy import Column, String, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin, generate_uuid


class Resin(Base, TimestampMixin):
    """Resin inventory model"""
    __tablename__ = "resin"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    color = Column(String(100), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20), nullable=False, default="kg")
    cost_per_unit = Column(Numeric(10, 2), nullable=False)
    purchase_date = Column(Date, nullable=False)
    purchase_source = Column(String(255))
    notes = Column(String(1000))


class PaintBottle(Base, TimestampMixin):
    """Paint bottle inventory model"""
    __tablename__ = "paint_bottles"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    color = Column(String(100), nullable=False)
    brand = Column(String(100), nullable=False)
    volume_ml = Column(Numeric(10, 2), nullable=False)
    current_volume_ml = Column(Numeric(10, 2), nullable=False)
    cost = Column(Numeric(10, 2), nullable=False)
    purchase_date = Column(Date, nullable=False)
    purchase_source = Column(String(255))
    notes = Column(String(1000))

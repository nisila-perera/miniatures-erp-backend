"""Painter model"""
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin, generate_uuid


class Painter(Base, TimestampMixin):
    """Painter model"""
    __tablename__ = "painters"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    is_active = Column(Boolean, default=True)

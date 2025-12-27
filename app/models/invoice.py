"""Invoice template model"""
from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin, generate_uuid


class InvoiceTemplate(Base, TimestampMixin):
    """Invoice template model"""
    __tablename__ = "invoice_templates"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)

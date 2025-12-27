"""Invoice template schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.base import BaseSchema, TimestampSchema


class InvoiceTemplateCreate(BaseModel):
    """Schema for creating an invoice template"""
    name: str = Field(..., max_length=255)
    subject: str = Field(..., max_length=500)
    body_html: str
    is_default: bool = False


class InvoiceTemplateUpdate(BaseModel):
    """Schema for updating an invoice template"""
    name: Optional[str] = Field(None, max_length=255)
    subject: Optional[str] = Field(None, max_length=500)
    body_html: Optional[str] = None
    is_default: Optional[bool] = None


class InvoiceTemplateResponse(BaseSchema, TimestampSchema):
    """Schema for invoice template response"""
    id: str
    name: str
    subject: str
    body_html: str
    is_default: bool

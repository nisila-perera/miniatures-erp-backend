"""Customer schemas"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from app.schemas.base import BaseSchema, TimestampSchema
from app.models.enums import CustomerSource


class CustomerCreate(BaseModel):
    """Schema for creating a customer"""
    name: str = Field(..., max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    source: CustomerSource = CustomerSource.ERP
    woocommerce_id: Optional[int] = None


class CustomerUpdate(BaseModel):
    """Schema for updating a customer"""
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)


class CustomerResponse(BaseSchema, TimestampSchema):
    """Schema for customer response"""
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]
    source: CustomerSource
    woocommerce_id: Optional[int]

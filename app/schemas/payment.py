"""Payment and PaymentMethod schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import date
from app.schemas.base import BaseSchema, TimestampSchema
from app.models.enums import CommissionType


class PaymentMethodCreate(BaseModel):
    """Schema for creating a payment method"""
    name: str = Field(..., max_length=255)
    commission_type: CommissionType
    commission_value: Decimal = Field(..., ge=0)
    is_active: bool = True


class PaymentMethodUpdate(BaseModel):
    """Schema for updating a payment method"""
    name: Optional[str] = Field(None, max_length=255)
    commission_type: Optional[CommissionType] = None
    commission_value: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class PaymentMethodResponse(BaseSchema, TimestampSchema):
    """Schema for payment method response"""
    id: str
    name: str
    commission_type: CommissionType
    commission_value: Decimal
    is_active: bool


class PaymentCreate(BaseModel):
    """Schema for creating a payment"""
    order_id: str
    payment_method_id: str
    amount: Decimal = Field(..., ge=0)
    payment_date: date
    reference_number: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)


class PaymentUpdate(BaseModel):
    """Schema for updating a payment"""
    payment_method_id: Optional[str] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    payment_date: Optional[date] = None
    reference_number: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)


class PaymentResponse(BaseSchema, TimestampSchema):
    """Schema for payment response"""
    id: str
    order_id: str
    payment_method_id: str
    amount: Decimal
    commission_amount: Decimal
    payment_date: date
    reference_number: Optional[str]
    notes: Optional[str]

"""Order, OrderItem, and OrderPainter schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, date
from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.customer import CustomerResponse
from app.schemas.payment import PaymentResponse, PaymentMethodResponse
from app.models.enums import OrderSource, OrderStatus, DiscountType


class OrderItemCreate(BaseModel):
    """Schema for creating an order item"""
    product_id: Optional[str] = None
    product_name: str = Field(..., max_length=255)
    product_category_id: str
    is_colored: bool = False
    dimensions: Optional[str] = Field(None, max_length=255)
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    discount_amount: Decimal = Field(default=0, ge=0)
    discount_type: Optional[DiscountType] = None
    discount_reason: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = Field(None, max_length=500)
    custom_description: Optional[str] = Field(None, max_length=1000)


class OrderItemResponse(BaseSchema, TimestampSchema):
    """Schema for order item response"""
    id: str
    order_id: str
    product_id: Optional[str]
    product_name: str
    product_category_id: str
    is_colored: bool
    dimensions: Optional[str]
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal
    discount_type: Optional[DiscountType]
    discount_reason: Optional[str]
    total_price: Decimal
    image_url: Optional[str]
    custom_description: Optional[str]


class OrderPainterCreate(BaseModel):
    """Schema for creating an order painter assignment"""
    painter_id: str
    assigned_date: date
    painting_cost: Decimal = Field(..., ge=0)
    notes: Optional[str] = Field(None, max_length=1000)


class OrderPainterResponse(BaseSchema, TimestampSchema):
    """Schema for order painter response"""
    id: str
    order_id: str
    painter_id: str
    painter_name: Optional[str] = None
    assigned_date: date
    painting_cost: Decimal
    notes: Optional[str]


class OrderCreate(BaseModel):
    """Schema for creating an order"""
    order_number: str = Field(..., max_length=50)
    source: OrderSource
    status: Optional[OrderStatus] = None
    customer_id: str
    order_date: datetime = Field(default_factory=datetime.utcnow)
    discount_amount: Decimal = Field(default=0, ge=0)
    discount_type: Optional[DiscountType] = None
    discount_reason: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=2000)
    woocommerce_id: Optional[int] = None
    items: List[OrderItemCreate] = []


class OrderUpdate(BaseModel):
    """Schema for updating an order"""
    status: Optional[OrderStatus] = None
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    discount_type: Optional[DiscountType] = None
    discount_reason: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=2000)


class PaymentWithMethodResponse(BaseSchema, TimestampSchema):
    """Schema for payment response with payment method details"""
    id: str
    order_id: str
    payment_method_id: str
    amount: Decimal
    commission_amount: Decimal
    payment_date: date
    reference_number: Optional[str]
    notes: Optional[str]
    payment_method: Optional[PaymentMethodResponse] = None


class OrderResponse(BaseSchema, TimestampSchema):
    """Schema for order response"""
    id: str
    order_number: str
    source: OrderSource
    status: OrderStatus
    customer_id: str
    order_date: datetime
    subtotal: Decimal
    discount_amount: Decimal
    discount_type: Optional[DiscountType]
    discount_reason: Optional[str]
    total_amount: Decimal
    paid_amount: Decimal
    balance: Decimal
    is_fully_paid: bool
    notes: Optional[str]
    woocommerce_id: Optional[int]
    items: List[OrderItemResponse] = []
    payments: List[PaymentWithMethodResponse] = []
    painters: List[OrderPainterResponse] = []
    customer: Optional[CustomerResponse] = None

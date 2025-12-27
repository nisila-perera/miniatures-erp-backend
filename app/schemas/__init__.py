"""Pydantic schemas for request/response validation"""
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse,
    OrderItemCreate, OrderItemResponse,
    OrderPainterCreate, OrderPainterResponse
)
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductCategoryCreate, ProductCategoryUpdate, ProductCategoryResponse
)
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.schemas.payment import (
    PaymentCreate, PaymentResponse,
    PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse
)
from app.schemas.painter import PainterCreate, PainterUpdate, PainterResponse
from app.schemas.inventory import (
    ResinCreate, ResinUpdate, ResinResponse,
    PaintBottleCreate, PaintBottleUpdate, PaintBottleResponse
)
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app.schemas.invoice import InvoiceTemplateCreate, InvoiceTemplateUpdate, InvoiceTemplateResponse

__all__ = [
    "OrderCreate", "OrderUpdate", "OrderResponse",
    "OrderItemCreate", "OrderItemResponse",
    "OrderPainterCreate", "OrderPainterResponse",
    "ProductCreate", "ProductUpdate", "ProductResponse",
    "ProductCategoryCreate", "ProductCategoryUpdate", "ProductCategoryResponse",
    "CustomerCreate", "CustomerUpdate", "CustomerResponse",
    "PaymentCreate", "PaymentResponse",
    "PaymentMethodCreate", "PaymentMethodUpdate", "PaymentMethodResponse",
    "PainterCreate", "PainterUpdate", "PainterResponse",
    "ResinCreate", "ResinUpdate", "ResinResponse",
    "PaintBottleCreate", "PaintBottleUpdate", "PaintBottleResponse",
    "ExpenseCreate", "ExpenseUpdate", "ExpenseResponse",
    "InvoiceTemplateCreate", "InvoiceTemplateUpdate", "InvoiceTemplateResponse",
]

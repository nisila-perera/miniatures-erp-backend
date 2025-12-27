"""Order API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.file_upload import save_uploaded_image
from app.services.order import OrderService
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderPainterCreate,
    OrderPainterResponse,
    OrderItemCreate,
    OrderItemResponse
)
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment import PaymentService
from app.models.enums import OrderSource, OrderStatus

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    """Create a new order"""
    service = OrderService(db)
    order = service.create_order(order_data)
    return order


@router.get("", response_model=List[OrderResponse])
def get_orders(
    source: Optional[OrderSource] = Query(None, description="Filter by order source"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    db: Session = Depends(get_db)
):
    """Get all orders with optional filtering"""
    service = OrderService(db)
    orders = service.get_orders(source=source, status=status)
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    db: Session = Depends(get_db)
):
    """Get an order by ID"""
    service = OrderService(db)
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: str,
    order_data: OrderUpdate,
    db: Session = Depends(get_db)
):
    """Update an order"""
    service = OrderService(db)
    order = service.update_order(order_id, order_data)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.delete("/{order_id}", status_code=204)
def delete_order(
    order_id: str,
    db: Session = Depends(get_db)
):
    """Delete an order"""
    service = OrderService(db)
    success = service.delete_order(order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")


@router.post("/{order_id}/painters", response_model=OrderPainterResponse, status_code=201)
def assign_painter(
    order_id: str,
    painter_data: OrderPainterCreate,
    db: Session = Depends(get_db)
):
    """Assign a painter to an order"""
    service = OrderService(db)
    painter_assignment = service.assign_painter(order_id, painter_data)
    if not painter_assignment:
        raise HTTPException(status_code=404, detail="Order not found")
    return painter_assignment


@router.get("/{order_id}/painters", response_model=List[OrderPainterResponse])
def get_order_painters(
    order_id: str,
    db: Session = Depends(get_db)
):
    """Get all painter assignments for an order"""
    service = OrderService(db)
    painters = service.get_order_painters(order_id)
    return painters


@router.post("/{order_id}/items", response_model=OrderItemResponse, status_code=201)
def add_order_item(
    order_id: str,
    item_data: OrderItemCreate,
    db: Session = Depends(get_db)
):
    """Add an item to an order"""
    service = OrderService(db)
    item = service.add_order_item(order_id, item_data)
    if not item:
        raise HTTPException(status_code=404, detail="Order not found")
    return item


@router.post("/upload-image", status_code=201)
async def upload_order_item_image(
    file: UploadFile = File(...)
):
    """Upload an image for a custom order item"""
    image_url = await save_uploaded_image(file)
    return {"image_url": image_url}


@router.post("/{order_id}/payments", response_model=PaymentResponse, status_code=201)
def record_payment(
    order_id: str,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    """Record a payment for an order"""
    # Ensure the order_id in the path matches the payment data
    if payment_data.order_id != order_id:
        raise HTTPException(status_code=400, detail="Order ID mismatch")
    
    service = PaymentService(db)
    payment = service.create_payment(payment_data)
    return payment


@router.get("/{order_id}/payments", response_model=List[PaymentResponse])
def get_order_payments(
    order_id: str,
    db: Session = Depends(get_db)
):
    """Get all payments for an order"""
    service = PaymentService(db)
    payments = service.get_payments_by_order(order_id)
    return payments

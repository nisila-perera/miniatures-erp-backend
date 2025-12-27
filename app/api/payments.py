"""Payment API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.services.payment import PaymentService
from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse, status_code=201)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    """Create a new payment"""
    service = PaymentService(db)
    payment = service.create_payment(payment_data)
    return payment


@router.get("", response_model=List[PaymentResponse])
def get_payments(
    order_id: str = Query(None, description="Filter by order ID"),
    db: Session = Depends(get_db)
):
    """Get all payments with optional filtering by order"""
    service = PaymentService(db)
    if order_id:
        payments = service.get_payments_by_order(order_id)
    else:
        payments = service.get_all_payments()
    return payments


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str,
    db: Session = Depends(get_db)
):
    """Get a payment by ID"""
    service = PaymentService(db)
    payment = service.get_payment(payment_id)
    return payment


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: str,
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db)
):
    """Update a payment"""
    service = PaymentService(db)
    payment = service.update_payment(payment_id, payment_data)
    return payment


@router.delete("/{payment_id}", status_code=204)
def delete_payment(
    payment_id: str,
    db: Session = Depends(get_db)
):
    """Delete a payment"""
    service = PaymentService(db)
    service.delete_payment(payment_id)

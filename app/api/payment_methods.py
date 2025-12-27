"""Payment method API endpoints"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.payment_method import PaymentMethodService
from app.schemas.payment import PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse

router = APIRouter(prefix="/api/payment-methods", tags=["Payment Methods"])


@router.post("", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
def create_payment_method(
    payment_method_data: PaymentMethodCreate,
    db: Session = Depends(get_db)
):
    """Create a new payment method"""
    service = PaymentMethodService(db)
    return service.create_payment_method(payment_method_data)


@router.get("", response_model=List[PaymentMethodResponse])
def get_payment_methods(db: Session = Depends(get_db)):
    """Get all payment methods"""
    service = PaymentMethodService(db)
    return service.get_all_payment_methods()


@router.get("/{payment_method_id}", response_model=PaymentMethodResponse)
def get_payment_method(payment_method_id: str, db: Session = Depends(get_db)):
    """Get a payment method by ID"""
    service = PaymentMethodService(db)
    return service.get_payment_method(payment_method_id)


@router.put("/{payment_method_id}", response_model=PaymentMethodResponse)
def update_payment_method(
    payment_method_id: str,
    payment_method_data: PaymentMethodUpdate,
    db: Session = Depends(get_db)
):
    """Update a payment method"""
    service = PaymentMethodService(db)
    return service.update_payment_method(payment_method_id, payment_method_data)


@router.delete("/{payment_method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_method(payment_method_id: str, db: Session = Depends(get_db)):
    """Delete a payment method"""
    service = PaymentMethodService(db)
    service.delete_payment_method(payment_method_id)

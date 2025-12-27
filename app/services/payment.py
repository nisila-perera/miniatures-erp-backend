"""Payment service for business logic"""
from typing import List
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.payment import PaymentRepository
from app.repositories.order import OrderRepository
from app.services.payment_method import PaymentMethodService
from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse


class PaymentService:
    """Service for payment business logic"""
    
    def __init__(self, db: Session):
        self.repository = PaymentRepository(db)
        self.order_repository = OrderRepository(db)
        self.payment_method_service = PaymentMethodService(db)
        self.db = db
    
    def create_payment(self, payment_data: PaymentCreate) -> PaymentResponse:
        """Create a new payment and update order balance"""
        # Validate order exists
        order = self.order_repository.get_by_id(payment_data.order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id {payment_data.order_id} not found"
            )
        
        # Validate payment amount
        if payment_data.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount must be greater than zero"
            )
        
        # Calculate commission
        commission_amount = self.payment_method_service.calculate_commission(
            payment_data.payment_method_id,
            payment_data.amount
        )
        
        # Create payment directly with commission
        from app.models.payment import Payment
        payment = Payment(
            **payment_data.model_dump(),
            commission_amount=commission_amount
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        # Update order paid amount and balance
        self._update_order_balance(payment_data.order_id)
        
        return PaymentResponse.model_validate(payment)
    
    def get_payment(self, payment_id: str) -> PaymentResponse:
        """Get a payment by ID"""
        payment = self.repository.get_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment with id {payment_id} not found"
            )
        return PaymentResponse.model_validate(payment)
    
    def get_payments_by_order(self, order_id: str) -> List[PaymentResponse]:
        """Get all payments for an order"""
        payments = self.repository.get_by_order_id(order_id)
        return [PaymentResponse.model_validate(p) for p in payments]
    
    def get_all_payments(self) -> List[PaymentResponse]:
        """Get all payments"""
        payments = self.repository.get_all()
        return [PaymentResponse.model_validate(p) for p in payments]
    
    def update_payment(self, payment_id: str, payment_data: PaymentUpdate) -> PaymentResponse:
        """Update a payment"""
        # Get existing payment
        existing_payment = self.repository.get_by_id(payment_id)
        if not existing_payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment with id {payment_id} not found"
            )
        
        # If amount or payment method changed, recalculate commission
        if payment_data.amount is not None or payment_data.payment_method_id is not None:
            payment_method_id = payment_data.payment_method_id or existing_payment.payment_method_id
            amount = payment_data.amount or existing_payment.amount
            
            commission_amount = self.payment_method_service.calculate_commission(
                payment_method_id,
                amount
            )
            
            # Add commission to update data
            payment_dict = payment_data.model_dump(exclude_unset=True)
            payment_dict['commission_amount'] = commission_amount
            payment_data = PaymentUpdate(**payment_dict)
        
        payment = self.repository.update(payment_id, payment_data)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment with id {payment_id} not found"
            )
        
        # Update order balance
        self._update_order_balance(existing_payment.order_id)
        
        return PaymentResponse.model_validate(payment)
    
    def delete_payment(self, payment_id: str) -> None:
        """Delete a payment"""
        # Get payment to get order_id before deletion
        payment = self.repository.get_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment with id {payment_id} not found"
            )
        
        order_id = payment.order_id
        
        success = self.repository.delete(payment_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment with id {payment_id} not found"
            )
        
        # Update order balance after deletion
        self._update_order_balance(order_id)
    
    def _update_order_balance(self, order_id: str) -> None:
        """Update order paid amount, balance, and fully paid flag"""
        order = self.order_repository.get_by_id(order_id)
        if not order:
            return
        
        # Calculate total paid amount from all payments
        payments = self.repository.get_by_order_id(order_id)
        total_paid = sum(payment.amount for payment in payments)
        
        # Update order
        order.paid_amount = total_paid
        order.balance = order.total_amount - total_paid
        order.is_fully_paid = order.balance <= 0
        
        self.db.commit()

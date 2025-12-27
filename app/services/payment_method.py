"""Payment method service for business logic"""
from typing import List
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.payment_method import PaymentMethodRepository
from app.schemas.payment import PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse
from app.models.enums import CommissionType


class PaymentMethodService:
    """Service for payment method business logic"""
    
    def __init__(self, db: Session):
        self.repository = PaymentMethodRepository(db)
    
    def create_payment_method(self, payment_method_data: PaymentMethodCreate) -> PaymentMethodResponse:
        """Create a new payment method"""
        # Validate that name is not empty
        if not payment_method_data.name or not payment_method_data.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment method name cannot be empty"
            )
        
        # Validate commission value
        if payment_method_data.commission_value < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Commission value cannot be negative"
            )
        
        # Validate percentage commission is not greater than 100
        if payment_method_data.commission_type == CommissionType.PERCENTAGE and payment_method_data.commission_value > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Percentage commission cannot exceed 100%"
            )
        
        payment_method = self.repository.create(payment_method_data)
        return PaymentMethodResponse.model_validate(payment_method)
    
    def get_payment_method(self, payment_method_id: str) -> PaymentMethodResponse:
        """Get a payment method by ID"""
        payment_method = self.repository.get_by_id(payment_method_id)
        if not payment_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment method with id {payment_method_id} not found"
            )
        return PaymentMethodResponse.model_validate(payment_method)
    
    def get_all_payment_methods(self) -> List[PaymentMethodResponse]:
        """Get all payment methods"""
        payment_methods = self.repository.get_all()
        return [PaymentMethodResponse.model_validate(pm) for pm in payment_methods]
    
    def update_payment_method(self, payment_method_id: str, payment_method_data: PaymentMethodUpdate) -> PaymentMethodResponse:
        """Update a payment method"""
        # Validate that name is not empty if provided
        if payment_method_data.name is not None and (not payment_method_data.name or not payment_method_data.name.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment method name cannot be empty"
            )
        
        # Validate commission value if provided
        if payment_method_data.commission_value is not None and payment_method_data.commission_value < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Commission value cannot be negative"
            )
        
        # Get existing payment method to check commission type
        existing_pm = self.repository.get_by_id(payment_method_id)
        if not existing_pm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment method with id {payment_method_id} not found"
            )
        
        # Determine the commission type to validate against
        commission_type = payment_method_data.commission_type if payment_method_data.commission_type is not None else existing_pm.commission_type
        commission_value = payment_method_data.commission_value if payment_method_data.commission_value is not None else existing_pm.commission_value
        
        # Validate percentage commission is not greater than 100
        if commission_type == CommissionType.PERCENTAGE and commission_value > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Percentage commission cannot exceed 100%"
            )
        
        payment_method = self.repository.update(payment_method_id, payment_method_data)
        if not payment_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment method with id {payment_method_id} not found"
            )
        return PaymentMethodResponse.model_validate(payment_method)
    
    def delete_payment_method(self, payment_method_id: str) -> None:
        """Delete a payment method"""
        success = self.repository.delete(payment_method_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment method with id {payment_method_id} not found"
            )
    
    def calculate_commission(self, payment_method_id: str, amount: Decimal) -> Decimal:
        """Calculate commission for a payment based on payment method"""
        payment_method = self.repository.get_by_id(payment_method_id)
        if not payment_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment method with id {payment_method_id} not found"
            )
        
        if payment_method.commission_type == CommissionType.FIXED:
            return payment_method.commission_value
        else:  # PERCENTAGE
            return (amount * payment_method.commission_value) / Decimal('100')

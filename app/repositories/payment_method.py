"""Payment method repository for database operations"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.payment import PaymentMethod
from app.schemas.payment import PaymentMethodCreate, PaymentMethodUpdate


class PaymentMethodRepository:
    """Repository for payment method database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, payment_method_data: PaymentMethodCreate) -> PaymentMethod:
        """Create a new payment method"""
        payment_method = PaymentMethod(**payment_method_data.model_dump())
        self.db.add(payment_method)
        self.db.commit()
        self.db.refresh(payment_method)
        return payment_method
    
    def get_by_id(self, payment_method_id: str) -> Optional[PaymentMethod]:
        """Get a payment method by ID"""
        return self.db.query(PaymentMethod).filter(PaymentMethod.id == payment_method_id).first()
    
    def get_all(self) -> List[PaymentMethod]:
        """Get all payment methods"""
        return self.db.query(PaymentMethod).all()
    
    def update(self, payment_method_id: str, payment_method_data: PaymentMethodUpdate) -> Optional[PaymentMethod]:
        """Update a payment method"""
        payment_method = self.get_by_id(payment_method_id)
        if not payment_method:
            return None
        
        update_data = payment_method_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payment_method, field, value)
        
        self.db.commit()
        self.db.refresh(payment_method)
        return payment_method
    
    def delete(self, payment_method_id: str) -> bool:
        """Delete a payment method"""
        payment_method = self.get_by_id(payment_method_id)
        if not payment_method:
            return False
        
        self.db.delete(payment_method)
        self.db.commit()
        return True

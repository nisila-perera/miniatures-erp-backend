"""Payment repository for database operations"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate


class PaymentRepository:
    """Repository for payment database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, payment_data: PaymentCreate) -> Payment:
        """Create a new payment"""
        payment = Payment(**payment_data.model_dump())
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def get_by_id(self, payment_id: str) -> Optional[Payment]:
        """Get a payment by ID"""
        return self.db.query(Payment).filter(Payment.id == payment_id).first()
    
    def get_by_order_id(self, order_id: str) -> List[Payment]:
        """Get all payments for an order"""
        return self.db.query(Payment).filter(Payment.order_id == order_id).all()
    
    def get_all(self) -> List[Payment]:
        """Get all payments"""
        return self.db.query(Payment).all()
    
    def update(self, payment_id: str, payment_data: PaymentUpdate) -> Optional[Payment]:
        """Update a payment"""
        payment = self.get_by_id(payment_id)
        if not payment:
            return None
        
        update_data = payment_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payment, field, value)
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def delete(self, payment_id: str) -> bool:
        """Delete a payment"""
        payment = self.get_by_id(payment_id)
        if not payment:
            return False
        
        self.db.delete(payment)
        self.db.commit()
        return True

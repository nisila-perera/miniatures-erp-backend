"""Customer repository for database operations"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerRepository:
    """Repository for customer database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, customer_data: CustomerCreate) -> Customer:
        """Create a new customer"""
        customer = Customer(**customer_data.model_dump())
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer
    
    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get a customer by ID"""
        return self.db.query(Customer).filter(Customer.id == customer_id).first()
    
    def get_all(self) -> List[Customer]:
        """Get all customers"""
        return self.db.query(Customer).all()
    
    def update(self, customer_id: str, customer_data: CustomerUpdate) -> Optional[Customer]:
        """Update a customer"""
        customer = self.get_by_id(customer_id)
        if not customer:
            return None
        
        update_data = customer_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        
        self.db.commit()
        self.db.refresh(customer)
        return customer
    
    def delete(self, customer_id: str) -> bool:
        """Delete a customer"""
        customer = self.get_by_id(customer_id)
        if not customer:
            return False
        
        self.db.delete(customer)
        self.db.commit()
        return True
    
    def get_by_woocommerce_id(self, woocommerce_id: int) -> Optional[Customer]:
        """Get a customer by WooCommerce ID"""
        return self.db.query(Customer).filter(Customer.woocommerce_id == woocommerce_id).first()

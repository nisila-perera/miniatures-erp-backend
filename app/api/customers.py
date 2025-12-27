"""Customer API endpoints"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.customer import CustomerService
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.schemas.order import OrderResponse

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db)
):
    """Create a new customer"""
    service = CustomerService(db)
    return service.create_customer(customer_data)


@router.get("", response_model=List[CustomerResponse])
def get_customers(db: Session = Depends(get_db)):
    """Get all customers"""
    service = CustomerService(db)
    return service.get_all_customers()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """Get a customer by ID"""
    service = CustomerService(db)
    return service.get_customer(customer_id)


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: str,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db)
):
    """Update a customer"""
    service = CustomerService(db)
    return service.update_customer(customer_id, customer_data)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: str, db: Session = Depends(get_db)):
    """Delete a customer"""
    service = CustomerService(db)
    service.delete_customer(customer_id)


@router.get("/{customer_id}/orders", response_model=List[OrderResponse])
def get_customer_orders(customer_id: str, db: Session = Depends(get_db)):
    """Get order history for a customer"""
    service = CustomerService(db)
    return service.get_customer_orders(customer_id)

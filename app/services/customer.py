"""Customer service for business logic"""
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.schemas.order import OrderResponse


class CustomerService:
    """Service for customer business logic"""
    
    def __init__(self, db: Session):
        self.repository = CustomerRepository(db)
    
    def create_customer(self, customer_data: CustomerCreate) -> CustomerResponse:
        """Create a new customer"""
        # Validate that name is not empty
        if not customer_data.name or not customer_data.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer name cannot be empty"
            )
        
        customer = self.repository.create(customer_data)
        return CustomerResponse.model_validate(customer)
    
    def get_customer(self, customer_id: str) -> CustomerResponse:
        """Get a customer by ID"""
        customer = self.repository.get_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {customer_id} not found"
            )
        return CustomerResponse.model_validate(customer)
    
    def get_all_customers(self) -> List[CustomerResponse]:
        """Get all customers"""
        customers = self.repository.get_all()
        return [CustomerResponse.model_validate(cust) for cust in customers]
    
    def update_customer(self, customer_id: str, customer_data: CustomerUpdate) -> CustomerResponse:
        """Update a customer"""
        # Get the customer first to check if it exists
        customer = self.repository.get_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {customer_id} not found"
            )
        
        # Validate that name is not empty if provided
        if customer_data.name is not None and (not customer_data.name or not customer_data.name.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer name cannot be empty"
            )
        
        updated_customer = self.repository.update(customer_id, customer_data)
        return CustomerResponse.model_validate(updated_customer)
    
    def delete_customer(self, customer_id: str) -> None:
        """Delete a customer"""
        customer = self.repository.get_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {customer_id} not found"
            )
        
        success = self.repository.delete(customer_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {customer_id} not found"
            )
    
    def get_customer_orders(self, customer_id: str) -> List[OrderResponse]:
        """Get order history for a customer"""
        customer = self.repository.get_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {customer_id} not found"
            )
        
        # Return orders associated with this customer
        return [OrderResponse.model_validate(order) for order in customer.orders]

"""Expense service for business logic"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.expense import ExpenseRepository
from app.models.enums import ExpenseCategory
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse


class ExpenseService:
    """Service for expense business logic"""
    
    def __init__(self, db: Session):
        self.repository = ExpenseRepository(db)
    
    def create_expense(self, expense_data: ExpenseCreate) -> ExpenseResponse:
        """Create a new expense"""
        # Validate that required fields are not empty
        if not expense_data.description or not expense_data.description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expense description cannot be empty"
            )
        
        # Category is already validated by Pydantic as it's a required field
        # Amount is already validated by Pydantic (gt=0)
        # expense_date is already validated by Pydantic as a required field
        
        expense = self.repository.create(expense_data)
        return ExpenseResponse.model_validate(expense)
    
    def get_expense(self, expense_id: str) -> ExpenseResponse:
        """Get an expense by ID"""
        expense = self.repository.get_by_id(expense_id)
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense with id {expense_id} not found"
            )
        return ExpenseResponse.model_validate(expense)
    
    def get_all_expenses(
        self,
        category: Optional[ExpenseCategory] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[ExpenseResponse]:
        """Get all expenses with optional filtering"""
        expenses = self.repository.get_all(category, start_date, end_date)
        return [ExpenseResponse.model_validate(exp) for exp in expenses]
    
    def update_expense(self, expense_id: str, expense_data: ExpenseUpdate) -> ExpenseResponse:
        """Update an expense"""
        # Get the expense first to check if it exists
        expense = self.repository.get_by_id(expense_id)
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense with id {expense_id} not found"
            )
        
        # Validate that description is not empty if provided
        if expense_data.description is not None and (not expense_data.description or not expense_data.description.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expense description cannot be empty"
            )
        
        updated_expense = self.repository.update(expense_id, expense_data)
        return ExpenseResponse.model_validate(updated_expense)
    
    def delete_expense(self, expense_id: str) -> None:
        """Delete an expense"""
        expense = self.repository.get_by_id(expense_id)
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense with id {expense_id} not found"
            )
        
        success = self.repository.delete(expense_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense with id {expense_id} not found"
            )

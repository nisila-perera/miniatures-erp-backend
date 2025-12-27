"""Expense repository for database operations"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from app.models.expense import Expense
from app.models.enums import ExpenseCategory
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


class ExpenseRepository:
    """Repository for expense database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, expense_data: ExpenseCreate) -> Expense:
        """Create a new expense"""
        expense = Expense(**expense_data.model_dump())
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense
    
    def get_by_id(self, expense_id: str) -> Optional[Expense]:
        """Get an expense by ID"""
        return self.db.query(Expense).filter(Expense.id == expense_id).first()
    
    def get_all(
        self,
        category: Optional[ExpenseCategory] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Expense]:
        """Get all expenses with optional filtering"""
        query = self.db.query(Expense)
        
        # Filter by category if provided
        if category:
            query = query.filter(Expense.category == category)
        
        # Filter by date range if provided
        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)
        
        return query.all()
    
    def update(self, expense_id: str, expense_data: ExpenseUpdate) -> Optional[Expense]:
        """Update an expense"""
        expense = self.get_by_id(expense_id)
        if not expense:
            return None
        
        update_data = expense_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(expense, field, value)
        
        self.db.commit()
        self.db.refresh(expense)
        return expense
    
    def delete(self, expense_id: str) -> bool:
        """Delete an expense"""
        expense = self.get_by_id(expense_id)
        if not expense:
            return False
        
        self.db.delete(expense)
        self.db.commit()
        return True

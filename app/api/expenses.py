"""Expense API endpoints"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.expense import ExpenseService
from app.models.enums import ExpenseCategory
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db)
):
    """Create a new expense"""
    service = ExpenseService(db)
    return service.create_expense(expense_data)


@router.get("", response_model=List[ExpenseResponse])
def get_expenses(
    category: Optional[ExpenseCategory] = Query(None, description="Filter by expense category"),
    start_date: Optional[date] = Query(None, description="Filter by start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (inclusive)"),
    db: Session = Depends(get_db)
):
    """Get all expenses with optional filtering by category and date range"""
    service = ExpenseService(db)
    return service.get_all_expenses(category, start_date, end_date)


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: str, db: Session = Depends(get_db)):
    """Get an expense by ID"""
    service = ExpenseService(db)
    return service.get_expense(expense_id)


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: str,
    expense_data: ExpenseUpdate,
    db: Session = Depends(get_db)
):
    """Update an expense"""
    service = ExpenseService(db)
    return service.update_expense(expense_id, expense_data)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: str, db: Session = Depends(get_db)):
    """Delete an expense"""
    service = ExpenseService(db)
    service.delete_expense(expense_id)

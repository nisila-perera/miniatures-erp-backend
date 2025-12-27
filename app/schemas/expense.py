"""Expense schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import date
from app.schemas.base import BaseSchema, TimestampSchema
from app.models.enums import ExpenseCategory


class ExpenseCreate(BaseModel):
    """Schema for creating an expense"""
    category: ExpenseCategory
    amount: Decimal = Field(..., gt=0)
    expense_date: date
    description: str = Field(..., max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)


class ExpenseUpdate(BaseModel):
    """Schema for updating an expense"""
    category: Optional[ExpenseCategory] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    expense_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)


class ExpenseResponse(BaseSchema, TimestampSchema):
    """Schema for expense response"""
    id: str
    category: ExpenseCategory
    amount: Decimal
    expense_date: date
    description: str
    notes: Optional[str]

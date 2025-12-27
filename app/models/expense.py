"""Expense model"""
from sqlalchemy import Column, String, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID, ENUM
from app.models.base import Base, TimestampMixin, generate_uuid
from app.models.enums import ExpenseCategory


class Expense(Base, TimestampMixin):
    """Expense model"""
    __tablename__ = "expenses"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    category = Column(ENUM(ExpenseCategory, name="expense_category"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    expense_date = Column(Date, nullable=False)
    description = Column(String(500), nullable=False)
    notes = Column(String(1000))

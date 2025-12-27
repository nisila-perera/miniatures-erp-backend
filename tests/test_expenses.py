"""Unit tests for expense management"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.expense import Expense
from app.models.enums import ExpenseCategory


@pytest.fixture
def client(db_session):
    """Create a test client with database session override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_expense(client, db_session):
    """Test creating an expense"""
    expense_data = {
        "category": "materials",
        "amount": 150.50,
        "expense_date": date.today().isoformat(),
        "description": "Test expense",
        "notes": "Test notes"
    }
    
    response = client.post("/api/expenses", json=expense_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["category"] == "materials"
    assert float(data["amount"]) == 150.50
    assert data["description"] == "Test expense"
    assert data["notes"] == "Test notes"
    
    # Clean up
    db_session.query(Expense).filter(Expense.id == data["id"]).delete()
    db_session.commit()


def test_get_expense(client, db_session):
    """Test retrieving an expense"""
    # Create an expense
    expense = Expense(
        category=ExpenseCategory.UTILITIES,
        amount=Decimal('75.00'),
        expense_date=date.today(),
        description="Test expense"
    )
    db_session.add(expense)
    db_session.commit()
    db_session.refresh(expense)
    
    # Retrieve the expense
    response = client.get(f"/api/expenses/{expense.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == str(expense.id)
    assert data["category"] == "utilities"
    assert float(data["amount"]) == 75.00
    
    # Clean up
    db_session.delete(expense)
    db_session.commit()


def test_get_all_expenses(client, db_session):
    """Test retrieving all expenses"""
    # Create multiple expenses
    expenses = [
        Expense(
            category=ExpenseCategory.MATERIALS,
            amount=Decimal('100.00'),
            expense_date=date.today(),
            description="Expense 1"
        ),
        Expense(
            category=ExpenseCategory.EQUIPMENT,
            amount=Decimal('200.00'),
            expense_date=date.today(),
            description="Expense 2"
        )
    ]
    
    for expense in expenses:
        db_session.add(expense)
    db_session.commit()
    
    # Retrieve all expenses
    response = client.get("/api/expenses")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 2
    
    # Clean up
    for expense in expenses:
        db_session.delete(expense)
    db_session.commit()


def test_filter_expenses_by_category(client, db_session):
    """Test filtering expenses by category"""
    # Create expenses with different categories
    expenses = [
        Expense(
            category=ExpenseCategory.MATERIALS,
            amount=Decimal('100.00'),
            expense_date=date.today(),
            description="Materials expense"
        ),
        Expense(
            category=ExpenseCategory.UTILITIES,
            amount=Decimal('50.00'),
            expense_date=date.today(),
            description="Utilities expense"
        )
    ]
    
    for expense in expenses:
        db_session.add(expense)
    db_session.commit()
    
    # Filter by materials category
    response = client.get("/api/expenses?category=materials")
    assert response.status_code == 200
    
    data = response.json()
    assert all(exp["category"] == "materials" for exp in data)
    
    # Clean up
    for expense in expenses:
        db_session.delete(expense)
    db_session.commit()


def test_filter_expenses_by_date_range(client, db_session):
    """Test filtering expenses by date range"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    
    # Create expenses with different dates
    expenses = [
        Expense(
            category=ExpenseCategory.MATERIALS,
            amount=Decimal('100.00'),
            expense_date=yesterday,
            description="Yesterday expense"
        ),
        Expense(
            category=ExpenseCategory.MATERIALS,
            amount=Decimal('150.00'),
            expense_date=today,
            description="Today expense"
        ),
        Expense(
            category=ExpenseCategory.MATERIALS,
            amount=Decimal('200.00'),
            expense_date=tomorrow,
            description="Tomorrow expense"
        )
    ]
    
    for expense in expenses:
        db_session.add(expense)
    db_session.commit()
    
    # Filter by date range (yesterday to today)
    response = client.get(
        f"/api/expenses?start_date={yesterday.isoformat()}&end_date={today.isoformat()}"
    )
    assert response.status_code == 200
    
    data = response.json()
    # Should only include yesterday and today expenses
    expense_dates = [date.fromisoformat(exp["expense_date"]) for exp in data]
    assert all(yesterday <= exp_date <= today for exp_date in expense_dates)
    
    # Clean up
    for expense in expenses:
        db_session.delete(expense)
    db_session.commit()


def test_update_expense(client, db_session):
    """Test updating an expense"""
    # Create an expense
    expense = Expense(
        category=ExpenseCategory.MATERIALS,
        amount=Decimal('100.00'),
        expense_date=date.today(),
        description="Original description"
    )
    db_session.add(expense)
    db_session.commit()
    db_session.refresh(expense)
    
    # Update the expense
    update_data = {
        "description": "Updated description",
        "amount": 150.00
    }
    
    response = client.put(f"/api/expenses/{expense.id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["description"] == "Updated description"
    assert float(data["amount"]) == 150.00
    
    # Clean up
    db_session.delete(expense)
    db_session.commit()


def test_delete_expense(client, db_session):
    """Test deleting an expense"""
    # Create an expense
    expense = Expense(
        category=ExpenseCategory.MATERIALS,
        amount=Decimal('100.00'),
        expense_date=date.today(),
        description="To be deleted"
    )
    db_session.add(expense)
    db_session.commit()
    db_session.refresh(expense)
    
    expense_id = expense.id
    
    # Delete the expense
    response = client.delete(f"/api/expenses/{expense_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    response = client.get(f"/api/expenses/{expense_id}")
    assert response.status_code == 404


def test_create_expense_without_category(client):
    """Test that creating an expense without category fails"""
    expense_data = {
        "amount": 100.00,
        "expense_date": date.today().isoformat(),
        "description": "Test expense"
    }
    
    response = client.post("/api/expenses", json=expense_data)
    assert response.status_code == 422  # Validation error


def test_create_expense_with_empty_description(client):
    """Test that creating an expense with empty description fails"""
    expense_data = {
        "category": "materials",
        "amount": 100.00,
        "expense_date": date.today().isoformat(),
        "description": "   "  # Empty/whitespace only
    }
    
    response = client.post("/api/expenses", json=expense_data)
    assert response.status_code == 400  # Bad request

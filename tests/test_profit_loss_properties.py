"""Property-based tests for profit and loss reporting"""
import pytest
import uuid
from decimal import Decimal
from datetime import date, datetime
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.order import Order
from app.models.customer import Customer
from app.models.product import ProductCategory
from app.models.expense import Expense
from app.models.enums import OrderSource, OrderStatus, CustomerSource, ExpenseCategory


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


def create_test_customer(db_session, seed: int) -> Customer:
    """Helper to create a test customer"""
    customer = Customer(
        name=f"Test Customer {seed}",
        email=f"customer{seed}@test.com",
        phone=f"555-{seed:04d}",
        address=f"{seed} Test St",
        city="Test City",
        postal_code=f"{seed:05d}",
        source=CustomerSource.ERP
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


def create_test_category(db_session, seed: int) -> ProductCategory:
    """Helper to create a test product category"""
    category = ProductCategory(
        name=f"Test Category {seed}",
        description=f"Test category description {seed}"
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


# Feature: miniatures-erp, Property 48: Profit and loss revenue calculation
# Validates: Requirements 15.1
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate a list of order amounts
    order_amounts=st.lists(
        st.decimals(min_value=Decimal('1.00'), max_value=Decimal('1000.00'), places=2),
        min_size=1,
        max_size=10
    ),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_profit_loss_revenue_calculation(client, db_session, order_amounts, seed):
    """
    Property: For any profit and loss statement for a given period, the total revenue 
    SHALL equal the sum of all order totals in that period.
    
    This property verifies that:
    1. The P&L report correctly sums all order totals as revenue
    2. No orders are missed or double-counted
    3. The calculation is accurate for any number of orders
    """
    # Create test data
    customer = create_test_customer(db_session, seed)
    category = create_test_category(db_session, seed)
    
    # Create orders with the generated amounts
    today = date.today()
    created_orders = []
    
    # Use UUID to ensure unique order numbers across all test runs
    unique_id = uuid.uuid4().hex[:8]
    for i, amount in enumerate(order_amounts):
        order = Order(
            order_number=f"ORD-{unique_id}-{i}",
            source=OrderSource.CUSTOM,
            status=OrderStatus.PENDING,
            customer_id=customer.id,
            order_date=datetime.combine(today, datetime.min.time()),
            subtotal=amount,
            total_amount=amount,
            paid_amount=Decimal('0'),
            balance=amount,
            is_fully_paid=False
        )
        db_session.add(order)
        created_orders.append(order)
    
    db_session.commit()
    
    # Calculate expected total revenue
    expected_revenue = sum(order_amounts)
    
    # Request P&L report for today
    report_request = {
        "date_range": "today"
    }
    
    response = client.post("/api/reports/profit-loss", json=report_request)
    
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text}"
    
    report = response.json()
    
    # Verify the total revenue matches the sum of all order amounts
    actual_revenue = Decimal(str(report["total_revenue"]))
    
    assert actual_revenue == expected_revenue, \
        f"P&L report revenue {actual_revenue} does not match expected sum {expected_revenue}"
    
    # Clean up
    for order in created_orders:
        db_session.delete(order)
    db_session.delete(category)
    db_session.delete(customer)
    db_session.commit()



# Feature: miniatures-erp, Property 49: Profit and loss expense calculation
# Validates: Requirements 15.2
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate a list of expense amounts
    expense_amounts=st.lists(
        st.decimals(min_value=Decimal('1.00'), max_value=Decimal('1000.00'), places=2),
        min_size=1,
        max_size=10
    ),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_profit_loss_expense_calculation(client, db_session, expense_amounts, seed):
    """
    Property: For any profit and loss statement for a given period, the total expenses 
    SHALL equal the sum of all expenses in that period.
    
    This property verifies that:
    1. The P&L report correctly sums all expense amounts
    2. No expenses are missed or double-counted
    3. The calculation is accurate for any number of expenses
    """
    # Create test data
    today = date.today()
    created_expenses = []
    
    for i, amount in enumerate(expense_amounts):
        expense = Expense(
            category=ExpenseCategory.MATERIALS,
            amount=amount,
            expense_date=today,
            description=f"Test expense {seed}-{i}"
        )
        db_session.add(expense)
        created_expenses.append(expense)
    
    db_session.commit()
    
    # Calculate expected total expenses
    expected_expenses = sum(expense_amounts)
    
    # Request P&L report for today
    report_request = {
        "date_range": "today"
    }
    
    response = client.post("/api/reports/profit-loss", json=report_request)
    
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text}"
    
    report = response.json()
    
    # Verify the total expenses matches the sum of all expense amounts
    actual_expenses = Decimal(str(report["total_expenses"]))
    
    assert actual_expenses == expected_expenses, \
        f"P&L report expenses {actual_expenses} does not match expected sum {expected_expenses}"
    
    # Clean up
    for expense in created_expenses:
        db_session.delete(expense)
    db_session.commit()



# Feature: miniatures-erp, Property 50: Profit and loss net profit calculation
# Validates: Requirements 15.3
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate lists of order and expense amounts
    order_amounts=st.lists(
        st.decimals(min_value=Decimal('1.00'), max_value=Decimal('1000.00'), places=2),
        min_size=1,
        max_size=10
    ),
    expense_amounts=st.lists(
        st.decimals(min_value=Decimal('1.00'), max_value=Decimal('1000.00'), places=2),
        min_size=1,
        max_size=10
    ),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_profit_loss_net_profit_calculation(client, db_session, order_amounts, expense_amounts, seed):
    """
    Property: For any profit and loss statement, the net profit SHALL equal 
    total revenue minus total expenses.
    
    This property verifies that:
    1. The P&L report correctly calculates net profit
    2. The calculation is accurate for any combination of revenue and expenses
    3. Net profit can be positive, negative, or zero
    """
    # Create test data
    customer = create_test_customer(db_session, seed)
    category = create_test_category(db_session, seed)
    
    # Create orders with the generated amounts
    today = date.today()
    created_orders = []
    
    # Use UUID to ensure unique order numbers across all test runs
    unique_id = uuid.uuid4().hex[:8]
    for i, amount in enumerate(order_amounts):
        order = Order(
            order_number=f"ORD-{unique_id}-{i}",
            source=OrderSource.CUSTOM,
            status=OrderStatus.PENDING,
            customer_id=customer.id,
            order_date=datetime.combine(today, datetime.min.time()),
            subtotal=amount,
            total_amount=amount,
            paid_amount=Decimal('0'),
            balance=amount,
            is_fully_paid=False
        )
        db_session.add(order)
        created_orders.append(order)
    
    # Create expenses with the generated amounts
    created_expenses = []
    
    for i, amount in enumerate(expense_amounts):
        expense = Expense(
            category=ExpenseCategory.MATERIALS,
            amount=amount,
            expense_date=today,
            description=f"Test expense {seed}-{i}"
        )
        db_session.add(expense)
        created_expenses.append(expense)
    
    db_session.commit()
    
    # Calculate expected values
    expected_revenue = sum(order_amounts)
    expected_expenses = sum(expense_amounts)
    expected_net_profit = expected_revenue - expected_expenses
    
    # Request P&L report for today
    report_request = {
        "date_range": "today"
    }
    
    response = client.post("/api/reports/profit-loss", json=report_request)
    
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text}"
    
    report = response.json()
    
    # Verify the net profit is calculated correctly
    actual_revenue = Decimal(str(report["total_revenue"]))
    actual_expenses = Decimal(str(report["total_expenses"]))
    actual_net_profit = Decimal(str(report["net_profit"]))
    
    # Verify revenue and expenses are correct
    assert actual_revenue == expected_revenue, \
        f"P&L report revenue {actual_revenue} does not match expected {expected_revenue}"
    
    assert actual_expenses == expected_expenses, \
        f"P&L report expenses {actual_expenses} does not match expected {expected_expenses}"
    
    # Verify net profit is calculated correctly
    assert actual_net_profit == expected_net_profit, \
        f"P&L report net profit {actual_net_profit} does not match expected {expected_net_profit} (revenue: {actual_revenue}, expenses: {actual_expenses})"
    
    # Also verify that net profit equals revenue minus expenses
    calculated_net_profit = actual_revenue - actual_expenses
    assert actual_net_profit == calculated_net_profit, \
        f"P&L report net profit {actual_net_profit} does not equal revenue minus expenses {calculated_net_profit}"
    
    # Clean up
    for order in created_orders:
        db_session.delete(order)
    for expense in created_expenses:
        db_session.delete(expense)
    db_session.delete(category)
    db_session.delete(customer)
    db_session.commit()



# Feature: miniatures-erp, Property 51: Profit and loss expense breakdown
# Validates: Requirements 15.5
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate expenses for different categories
    materials_expenses=st.lists(
        st.decimals(min_value=Decimal('1.00'), max_value=Decimal('500.00'), places=2),
        min_size=0,
        max_size=5
    ),
    utilities_expenses=st.lists(
        st.decimals(min_value=Decimal('1.00'), max_value=Decimal('500.00'), places=2),
        min_size=0,
        max_size=5
    ),
    equipment_expenses=st.lists(
        st.decimals(min_value=Decimal('1.00'), max_value=Decimal('500.00'), places=2),
        min_size=0,
        max_size=5
    ),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_profit_loss_expense_breakdown(client, db_session, materials_expenses, utilities_expenses, equipment_expenses, seed):
    """
    Property: For any profit and loss statement, expenses SHALL be correctly grouped 
    by category with accurate subtotals.
    
    This property verifies that:
    1. The P&L report correctly groups expenses by category
    2. Each category subtotal equals the sum of expenses in that category
    3. The sum of all category subtotals equals the total expenses
    """
    # Create test data
    today = date.today()
    created_expenses = []
    
    # Create materials expenses
    for i, amount in enumerate(materials_expenses):
        expense = Expense(
            category=ExpenseCategory.MATERIALS,
            amount=amount,
            expense_date=today,
            description=f"Materials expense {seed}-{i}"
        )
        db_session.add(expense)
        created_expenses.append(expense)
    
    # Create utilities expenses
    for i, amount in enumerate(utilities_expenses):
        expense = Expense(
            category=ExpenseCategory.UTILITIES,
            amount=amount,
            expense_date=today,
            description=f"Utilities expense {seed}-{i}"
        )
        db_session.add(expense)
        created_expenses.append(expense)
    
    # Create equipment expenses
    for i, amount in enumerate(equipment_expenses):
        expense = Expense(
            category=ExpenseCategory.EQUIPMENT,
            amount=amount,
            expense_date=today,
            description=f"Equipment expense {seed}-{i}"
        )
        db_session.add(expense)
        created_expenses.append(expense)
    
    db_session.commit()
    
    # Calculate expected values
    expected_materials_total = sum(materials_expenses)
    expected_utilities_total = sum(utilities_expenses)
    expected_equipment_total = sum(equipment_expenses)
    expected_total_expenses = expected_materials_total + expected_utilities_total + expected_equipment_total
    
    # Request P&L report for today
    report_request = {
        "date_range": "today"
    }
    
    response = client.post("/api/reports/profit-loss", json=report_request)
    
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text}"
    
    report = response.json()
    
    # Verify the total expenses is correct
    actual_total_expenses = Decimal(str(report["total_expenses"]))
    assert actual_total_expenses == expected_total_expenses, \
        f"P&L report total expenses {actual_total_expenses} does not match expected {expected_total_expenses}"
    
    # Verify the expense breakdown
    expense_breakdown = report["expense_breakdown"]
    
    # Create a dictionary for easy lookup
    breakdown_dict = {item["category"]: Decimal(str(item["amount"])) for item in expense_breakdown}
    
    # Verify materials category
    if materials_expenses:
        assert "materials" in breakdown_dict, "Materials category missing from breakdown"
        assert breakdown_dict["materials"] == expected_materials_total, \
            f"Materials breakdown {breakdown_dict['materials']} does not match expected {expected_materials_total}"
    
    # Verify utilities category
    if utilities_expenses:
        assert "utilities" in breakdown_dict, "Utilities category missing from breakdown"
        assert breakdown_dict["utilities"] == expected_utilities_total, \
            f"Utilities breakdown {breakdown_dict['utilities']} does not match expected {expected_utilities_total}"
    
    # Verify equipment category
    if equipment_expenses:
        assert "equipment" in breakdown_dict, "Equipment category missing from breakdown"
        assert breakdown_dict["equipment"] == expected_equipment_total, \
            f"Equipment breakdown {breakdown_dict['equipment']} does not match expected {expected_equipment_total}"
    
    # Verify that the sum of all breakdown amounts equals total expenses
    breakdown_sum = sum(breakdown_dict.values())
    assert breakdown_sum == expected_total_expenses, \
        f"Sum of expense breakdown {breakdown_sum} does not match total expenses {expected_total_expenses}"
    
    # Clean up
    for expense in created_expenses:
        db_session.delete(expense)
    db_session.commit()

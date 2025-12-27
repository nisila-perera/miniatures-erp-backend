"""Property-based tests for expense management"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck
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


# Feature: miniatures-erp, Property 37: Expense category requirement
# Validates: Requirements 11.1
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random expense data without category
    amount=st.decimals(min_value=Decimal('0.01'), max_value=Decimal('10000.00'), places=2),
    description=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_expense_category_requirement(client, db_session, amount, description, seed):
    """
    Property: For any expense, the system SHALL reject expenses without a category specified.
    
    This property verifies that:
    1. Expenses cannot be created without a category
    2. The API returns an appropriate error when category is missing
    3. Category is a required field that cannot be null or omitted
    """
    # Attempt to create an expense without a category
    # This should be rejected by the API
    expense_data = {
        "amount": float(amount),
        "expense_date": date.today().isoformat(),
        "description": description.strip() or "Test expense"
    }
    # Intentionally omit "category" field
    
    response = client.post("/api/expenses", json=expense_data)
    
    # The API should reject this request with a 422 (validation error)
    assert response.status_code == 422, \
        f"Expected status 422 for expense without category, got {response.status_code}: {response.text}"
    
    # Verify the error message indicates the category field is required
    error_detail = response.json()
    assert "detail" in error_detail, "Response should contain error details"
    
    # Check that the error is about the missing category field
    error_messages = str(error_detail["detail"]).lower()
    assert "category" in error_messages, \
        f"Error should mention 'category' field, got: {error_detail['detail']}"


# Feature: miniatures-erp, Property 38: Expense required fields
# Validates: Requirements 11.3
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random valid expense data
    category=st.sampled_from(list(ExpenseCategory)),
    amount=st.decimals(min_value=Decimal('0.01'), max_value=Decimal('10000.00'), places=2),
    days_offset=st.integers(min_value=-365, max_value=365),
    description=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
    notes=st.one_of(st.none(), st.text(max_size=200, alphabet=st.characters(blacklist_categories=('Cs', 'Cc')))),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_expense_required_fields(client, db_session, category, amount, days_offset, description, notes, seed):
    """
    Property: For any expense recorded, it SHALL have amount, date, and description stored.
    
    This property verifies that:
    1. All required fields (amount, date, description, category) are stored
    2. Retrieved expenses contain all required fields
    3. The stored values match the input values
    4. Optional fields (notes) are handled correctly
    """
    created_expense_id = None
    
    try:
        # Clean description to ensure it's not empty
        clean_description = description.strip() or "Test expense"
        clean_notes = notes.strip() if notes else None
        
        # Calculate expense date
        expense_date = date.today() + timedelta(days=days_offset)
        
        # Create an expense with all required fields
        expense_data = {
            "category": category.value,
            "amount": float(amount),
            "expense_date": expense_date.isoformat(),
            "description": clean_description,
            "notes": clean_notes
        }
        
        response = client.post("/api/expenses", json=expense_data)
        
        assert response.status_code == 201, \
            f"Expected status 201 for expense creation, got {response.status_code}: {response.text}"
        
        expense_response = response.json()
        created_expense_id = expense_response["id"]
        
        # Verify all required fields are present in the response
        assert "id" in expense_response, "Response should contain id"
        assert "category" in expense_response, "Response should contain category"
        assert "amount" in expense_response, "Response should contain amount"
        assert "expense_date" in expense_response, "Response should contain expense_date"
        assert "description" in expense_response, "Response should contain description"
        
        # Verify the values match what was sent
        assert expense_response["category"] == category.value, \
            f"Expected category {category.value}, got {expense_response['category']}"
        
        response_amount = Decimal(str(expense_response["amount"]))
        amount_diff = abs(amount - response_amount)
        assert amount_diff < Decimal('0.01'), \
            f"Expected amount {amount}, got {response_amount}"
        
        assert expense_response["expense_date"] == expense_date.isoformat(), \
            f"Expected date {expense_date.isoformat()}, got {expense_response['expense_date']}"
        
        assert expense_response["description"] == clean_description, \
            f"Expected description '{clean_description}', got '{expense_response['description']}'"
        
        # Verify notes field (optional)
        if clean_notes:
            assert expense_response["notes"] == clean_notes, \
                f"Expected notes '{clean_notes}', got '{expense_response['notes']}'"
        
        # Retrieve the expense and verify all fields are still present
        get_response = client.get(f"/api/expenses/{created_expense_id}")
        assert get_response.status_code == 200, \
            f"Expected status 200 for expense retrieval, got {get_response.status_code}"
        
        retrieved_expense = get_response.json()
        
        # Verify all required fields are present in retrieved expense
        assert retrieved_expense["id"] == created_expense_id
        assert retrieved_expense["category"] == category.value
        assert retrieved_expense["expense_date"] == expense_date.isoformat()
        assert retrieved_expense["description"] == clean_description
        
        retrieved_amount = Decimal(str(retrieved_expense["amount"]))
        amount_diff = abs(amount - retrieved_amount)
        assert amount_diff < Decimal('0.01'), \
            f"Retrieved amount {retrieved_amount} should match original {amount}"
    
    finally:
        # Clean up: delete the created expense
        if created_expense_id:
            try:
                db_session.query(Expense).filter(Expense.id == created_expense_id).delete()
                db_session.commit()
            except:
                pass


# Feature: miniatures-erp, Property 39: Expense filtering by category
# Validates: Requirements 11.5
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random expenses with different categories
    target_category=st.sampled_from(list(ExpenseCategory)),
    num_matching=st.integers(min_value=1, max_value=5),
    num_non_matching=st.integers(min_value=1, max_value=5),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_expense_filtering_by_category(client, db_session, target_category, num_matching, num_non_matching, seed):
    """
    Property: For any set of expenses and any category filter, all returned expenses SHALL have the specified category.
    
    This property verifies that:
    1. Filtering by category returns only expenses with that category
    2. No expenses with other categories are returned
    3. All expenses with the target category are returned
    4. The filter works correctly for all category types
    """
    import random
    random.seed(seed)
    
    created_expense_ids = []
    
    try:
        # Get all categories except the target
        other_categories = [cat for cat in ExpenseCategory if cat != target_category]
        
        # Create expenses with the target category
        matching_expense_ids = []
        for i in range(num_matching):
            expense_data = {
                "category": target_category.value,
                "amount": float(Decimal(str(random.uniform(10.0, 1000.0))).quantize(Decimal('0.01'))),
                "expense_date": date.today().isoformat(),
                "description": f"Matching expense {i+1}"
            }
            
            response = client.post("/api/expenses", json=expense_data)
            assert response.status_code == 201, \
                f"Failed to create matching expense: {response.text}"
            
            expense_id = response.json()["id"]
            created_expense_ids.append(expense_id)
            matching_expense_ids.append(expense_id)
        
        # Create expenses with other categories
        if other_categories:
            for i in range(num_non_matching):
                other_category = random.choice(other_categories)
                expense_data = {
                    "category": other_category.value,
                    "amount": float(Decimal(str(random.uniform(10.0, 1000.0))).quantize(Decimal('0.01'))),
                    "expense_date": date.today().isoformat(),
                    "description": f"Non-matching expense {i+1}"
                }
                
                response = client.post("/api/expenses", json=expense_data)
                assert response.status_code == 201, \
                    f"Failed to create non-matching expense: {response.text}"
                
                created_expense_ids.append(response.json()["id"])
        
        # Filter expenses by target category
        response = client.get(f"/api/expenses?category={target_category.value}")
        assert response.status_code == 200, \
            f"Expected status 200 for expense filtering, got {response.status_code}: {response.text}"
        
        filtered_expenses = response.json()
        
        # Verify all returned expenses have the target category
        for expense in filtered_expenses:
            assert expense["category"] == target_category.value, \
                f"Filtered expense has category {expense['category']}, expected {target_category.value}"
        
        # Verify all matching expenses are in the results
        filtered_ids = [exp["id"] for exp in filtered_expenses]
        for matching_id in matching_expense_ids:
            assert matching_id in filtered_ids, \
                f"Expense {matching_id} with category {target_category.value} should be in filtered results"
        
        # Verify the count matches
        assert len([exp for exp in filtered_expenses if exp["id"] in matching_expense_ids]) == num_matching, \
            f"Expected {num_matching} matching expenses, found {len([exp for exp in filtered_expenses if exp['id'] in matching_expense_ids])}"
    
    finally:
        # Clean up: delete all created expenses
        for expense_id in created_expense_ids:
            try:
                db_session.query(Expense).filter(Expense.id == expense_id).delete()
            except:
                pass
        db_session.commit()


# Feature: miniatures-erp, Property 40: Expense filtering by date range
# Validates: Requirements 11.6
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate random date range and expenses
    range_start_offset=st.integers(min_value=-30, max_value=0),
    range_days=st.integers(min_value=1, max_value=30),
    num_in_range=st.integers(min_value=1, max_value=5),
    num_before_range=st.integers(min_value=1, max_value=3),
    num_after_range=st.integers(min_value=1, max_value=3),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_expense_filtering_by_date_range(client, db_session, range_start_offset, range_days,
                                        num_in_range, num_before_range, num_after_range, seed):
    """
    Property: For any set of expenses and any date range, all returned expenses SHALL have dates within the specified range.
    
    This property verifies that:
    1. Filtering by date range returns only expenses within that range
    2. Expenses before the start date are excluded
    3. Expenses after the end date are excluded
    4. Expenses on the boundary dates are included
    5. The filter works correctly for all date ranges
    """
    import random
    random.seed(seed)
    
    created_expense_ids = []
    
    try:
        # Define the date range
        today = date.today()
        start_date = today + timedelta(days=range_start_offset)
        end_date = start_date + timedelta(days=range_days)
        
        # Create expenses within the range
        in_range_expense_ids = []
        for i in range(num_in_range):
            # Random date within range
            days_from_start = random.randint(0, range_days)
            expense_date = start_date + timedelta(days=days_from_start)
            
            expense_data = {
                "category": random.choice(list(ExpenseCategory)).value,
                "amount": float(Decimal(str(random.uniform(10.0, 1000.0))).quantize(Decimal('0.01'))),
                "expense_date": expense_date.isoformat(),
                "description": f"In-range expense {i+1}"
            }
            
            response = client.post("/api/expenses", json=expense_data)
            assert response.status_code == 201, \
                f"Failed to create in-range expense: {response.text}"
            
            expense_id = response.json()["id"]
            created_expense_ids.append(expense_id)
            in_range_expense_ids.append(expense_id)
        
        # Create expenses before the range
        for i in range(num_before_range):
            # Date before start_date
            days_before = random.randint(1, 30)
            expense_date = start_date - timedelta(days=days_before)
            
            expense_data = {
                "category": random.choice(list(ExpenseCategory)).value,
                "amount": float(Decimal(str(random.uniform(10.0, 1000.0))).quantize(Decimal('0.01'))),
                "expense_date": expense_date.isoformat(),
                "description": f"Before-range expense {i+1}"
            }
            
            response = client.post("/api/expenses", json=expense_data)
            assert response.status_code == 201, \
                f"Failed to create before-range expense: {response.text}"
            
            created_expense_ids.append(response.json()["id"])
        
        # Create expenses after the range
        for i in range(num_after_range):
            # Date after end_date
            days_after = random.randint(1, 30)
            expense_date = end_date + timedelta(days=days_after)
            
            expense_data = {
                "category": random.choice(list(ExpenseCategory)).value,
                "amount": float(Decimal(str(random.uniform(10.0, 1000.0))).quantize(Decimal('0.01'))),
                "expense_date": expense_date.isoformat(),
                "description": f"After-range expense {i+1}"
            }
            
            response = client.post("/api/expenses", json=expense_data)
            assert response.status_code == 201, \
                f"Failed to create after-range expense: {response.text}"
            
            created_expense_ids.append(response.json()["id"])
        
        # Filter expenses by date range
        response = client.get(
            f"/api/expenses?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )
        assert response.status_code == 200, \
            f"Expected status 200 for expense filtering, got {response.status_code}: {response.text}"
        
        filtered_expenses = response.json()
        
        # Verify all returned expenses are within the date range
        for expense in filtered_expenses:
            expense_date_str = expense["expense_date"]
            expense_date_obj = date.fromisoformat(expense_date_str)
            
            assert start_date <= expense_date_obj <= end_date, \
                f"Expense date {expense_date_obj} is outside range [{start_date}, {end_date}]"
        
        # Verify all in-range expenses are in the results
        filtered_ids = [exp["id"] for exp in filtered_expenses]
        for in_range_id in in_range_expense_ids:
            assert in_range_id in filtered_ids, \
                f"Expense {in_range_id} within date range should be in filtered results"
        
        # Verify the count matches
        assert len([exp for exp in filtered_expenses if exp["id"] in in_range_expense_ids]) == num_in_range, \
            f"Expected {num_in_range} in-range expenses, found {len([exp for exp in filtered_expenses if exp['id'] in in_range_expense_ids])}"
    
    finally:
        # Clean up: delete all created expenses
        for expense_id in created_expense_ids:
            try:
                db_session.query(Expense).filter(Expense.id == expense_id).delete()
            except:
                pass
        db_session.commit()

"""Property-based tests for material usage reporting"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from datetime import date, timedelta
from decimal import Decimal
from app.main import app
from app.core.database import get_db
from app.models.inventory import Resin, PaintBottle


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


# Feature: miniatures-erp, Property 52: Material usage resin grouping
# Validates: Requirements 16.1
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate multiple resin entries with some having the same color
    num_entries=st.integers(min_value=1, max_value=5),
    color_pool_size=st.integers(min_value=1, max_value=3),
    days_ago=st.integers(min_value=0, max_value=30)
)
def test_material_usage_resin_grouping(client, db_session, num_entries, color_pool_size, days_ago):
    """
    Property: For any material usage report, resin SHALL be grouped by color with accurate quantities.
    
    This property verifies that:
    1. Resin entries with the same color are grouped together
    2. The total quantity for each color is the sum of all entries with that color
    3. The grouping is accurate across all colors in the date range
    """
    created_resins = []
    
    try:
        # Create a pool of colors to use
        color_pool = [f"Color{i}" for i in range(color_pool_size)]
        
        # Track expected totals by color
        expected_by_color = {}
        
        # Create resin entries
        for i in range(num_entries):
            # Pick a color from the pool
            color = color_pool[i % color_pool_size]
            quantity = Decimal(str(10.0 + i))
            cost_per_unit = Decimal(str(5.0 + i))
            
            purchase_date = date.today() - timedelta(days=days_ago)
            
            resin_data = {
                "color": color,
                "quantity": float(quantity),
                "unit": "kg",
                "cost_per_unit": float(cost_per_unit),
                "purchase_date": purchase_date.isoformat()
            }
            
            create_response = client.post("/api/inventory/resin", json=resin_data)
            assert create_response.status_code == 201, \
                f"Failed to create resin entry {i}"
            
            created_data = create_response.json()
            created_resins.append(created_data["id"])
            
            # Track expected totals
            if color not in expected_by_color:
                expected_by_color[color] = {
                    "total_quantity": Decimal(0),
                    "total_cost": Decimal(0),
                    "unit": "kg"
                }
            
            expected_by_color[color]["total_quantity"] += quantity
            expected_by_color[color]["total_cost"] += quantity * cost_per_unit
        
        # Generate material usage report
        report_request = {
            "date_range": "custom",
            "start_date": (date.today() - timedelta(days=days_ago + 1)).isoformat(),
            "end_date": date.today().isoformat()
        }
        
        report_response = client.post("/api/reports/materials", json=report_request)
        
        assert report_response.status_code == 200, \
            f"Expected status 200 for report generation, got {report_response.status_code}"
        
        report_data = report_response.json()
        
        # Verify resin_by_color is present
        assert "resin_by_color" in report_data, \
            "Report should have resin_by_color field"
        
        resin_by_color = report_data["resin_by_color"]
        
        # Verify the number of color groups matches expected
        assert len(resin_by_color) == len(expected_by_color), \
            f"Expected {len(expected_by_color)} color groups, but got {len(resin_by_color)}"
        
        # Verify each color group has correct totals
        for resin_group in resin_by_color:
            color = resin_group["color"]
            
            assert color in expected_by_color, \
                f"Unexpected color '{color}' in report"
            
            expected = expected_by_color[color]
            
            # Verify total quantity
            actual_quantity = Decimal(str(resin_group["total_quantity"]))
            assert actual_quantity == expected["total_quantity"], \
                f"For color '{color}', expected total_quantity {expected['total_quantity']}, but got {actual_quantity}"
            
            # Verify total cost
            actual_cost = Decimal(str(resin_group["total_cost"]))
            assert actual_cost == expected["total_cost"], \
                f"For color '{color}', expected total_cost {expected['total_cost']}, but got {actual_cost}"
            
            # Verify unit
            assert resin_group["unit"] == expected["unit"], \
                f"For color '{color}', expected unit '{expected['unit']}', but got '{resin_group['unit']}'"
    
    finally:
        # Clean up: delete all created resins
        for resin_id in created_resins:
            db_session.query(Resin).filter(Resin.id == resin_id).delete()
        db_session.commit()


# Feature: miniatures-erp, Property 53: Material usage cost calculation
# Validates: Requirements 16.4
@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    # Generate multiple material entries - ensure at least one material
    num_resin=st.integers(min_value=0, max_value=3),
    num_paint=st.integers(min_value=0, max_value=3),
    days_ago=st.integers(min_value=0, max_value=30)
)
def test_material_usage_cost_calculation(client, db_session, num_resin, num_paint, days_ago):
    """
    Property: For any material usage report for a given period, the total material cost SHALL equal 
    the sum of all material costs in that period.
    
    This property verifies that:
    1. The total material cost includes both resin and paint costs
    2. The calculation is accurate (sum of all individual material costs)
    3. The cost calculation works correctly for any combination of materials
    """
    # Skip if no materials to create - filter at hypothesis level
    from hypothesis import assume
    assume(num_resin > 0 or num_paint > 0)
    
    created_resins = []
    created_paints = []
    
    try:
        
        expected_total_cost = Decimal(0)
        purchase_date = date.today() - timedelta(days=days_ago)
        
        # Create resin entries
        for i in range(num_resin):
            quantity = Decimal(str(10.0 + i))
            cost_per_unit = Decimal(str(5.0 + i))
            resin_cost = quantity * cost_per_unit
            
            resin_data = {
                "color": f"ResinColor{i}",
                "quantity": float(quantity),
                "unit": "kg",
                "cost_per_unit": float(cost_per_unit),
                "purchase_date": purchase_date.isoformat()
            }
            
            create_response = client.post("/api/inventory/resin", json=resin_data)
            assert create_response.status_code == 201, \
                f"Failed to create resin entry {i}"
            
            created_data = create_response.json()
            created_resins.append(created_data["id"])
            expected_total_cost += resin_cost
        
        # Create paint bottle entries
        for i in range(num_paint):
            paint_cost = Decimal(str(15.0 + i))
            
            paint_data = {
                "color": f"PaintColor{i}",
                "brand": f"Brand{i}",
                "volume_ml": 50.0,
                "current_volume_ml": 50.0,
                "cost": float(paint_cost),
                "purchase_date": purchase_date.isoformat()
            }
            
            create_response = client.post("/api/inventory/paint", json=paint_data)
            assert create_response.status_code == 201, \
                f"Failed to create paint entry {i}"
            
            created_data = create_response.json()
            created_paints.append(created_data["id"])
            expected_total_cost += paint_cost
        
        # Generate material usage report
        report_request = {
            "date_range": "custom",
            "start_date": (date.today() - timedelta(days=days_ago + 1)).isoformat(),
            "end_date": date.today().isoformat()
        }
        
        report_response = client.post("/api/reports/materials", json=report_request)
        
        assert report_response.status_code == 200, \
            f"Expected status 200 for report generation, got {report_response.status_code}"
        
        report_data = report_response.json()
        
        # Verify total_material_cost is present
        assert "total_material_cost" in report_data, \
            "Report should have total_material_cost field"
        
        actual_total_cost = Decimal(str(report_data["total_material_cost"]))
        
        # Verify the total cost matches expected
        assert actual_total_cost == expected_total_cost, \
            f"Expected total_material_cost {expected_total_cost}, but got {actual_total_cost}"
        
        # Verify the calculation by summing resin and paint costs from the report
        resin_cost_sum = sum(
            Decimal(str(r["total_cost"])) 
            for r in report_data.get("resin_by_color", [])
        )
        
        paint_cost_sum = sum(
            Decimal(str(p["cost"])) 
            for p in report_data.get("paint_bottles", [])
        )
        
        calculated_total = resin_cost_sum + paint_cost_sum
        
        assert actual_total_cost == calculated_total, \
            f"Total cost {actual_total_cost} should equal sum of resin ({resin_cost_sum}) and paint ({paint_cost_sum}) costs"
    
    finally:
        # Clean up: delete all created materials
        for resin_id in created_resins:
            db_session.query(Resin).filter(Resin.id == resin_id).delete()
        for paint_id in created_paints:
            db_session.query(PaintBottle).filter(PaintBottle.id == paint_id).delete()
        db_session.commit()

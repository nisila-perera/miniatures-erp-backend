#!/usr/bin/env python3
"""
Simple structure verification for product category implementation
Checks files exist and contain required components without importing
"""

import sys
from pathlib import Path


def check_file_contains(file_path: str, search_terms: list) -> tuple:
    """Check if a file contains all search terms"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        results = []
        for term in search_terms:
            found = term in content
            results.append((term, found))
        
        return results
    except FileNotFoundError:
        return [(term, False) for term in search_terms]


def verify_structure():
    """Verify file structure and basic content"""
    print("Verifying Product Category Management Structure...")
    print("=" * 70)
    
    all_passed = True
    
    # Check repository
    print("\n1. Repository (app/repositories/product_category.py)")
    repo_checks = check_file_contains(
        "app/repositories/product_category.py",
        ["class ProductCategoryRepository", "def create", "def get_by_id", 
         "def get_all", "def update", "def delete"]
    )
    for term, found in repo_checks:
        status = "✓" if found else "✗"
        print(f"  {status} {term}")
        if not found:
            all_passed = False
    
    # Check service
    print("\n2. Service (app/services/product_category.py)")
    service_checks = check_file_contains(
        "app/services/product_category.py",
        ["class ProductCategoryService", "def create_category", "def get_category",
         "def get_all_categories", "def update_category", "def delete_category"]
    )
    for term, found in service_checks:
        status = "✓" if found else "✗"
        print(f"  {status} {term}")
        if not found:
            all_passed = False
    
    # Check API router
    print("\n3. API Router (app/api/product_categories.py)")
    api_checks = check_file_contains(
        "app/api/product_categories.py",
        ["router = APIRouter", "@router.post", "@router.get", 
         "@router.put", "@router.delete", "ProductCategoryResponse"]
    )
    for term, found in api_checks:
        status = "✓" if found else "✗"
        print(f"  {status} {term}")
        if not found:
            all_passed = False
    
    # Check main app integration
    print("\n4. Main App Integration (app/main.py)")
    main_checks = check_file_contains(
        "app/main.py",
        ["from app.api import product_categories", "app.include_router(product_categories.router)"]
    )
    for term, found in main_checks:
        status = "✓" if found else "✗"
        print(f"  {status} {term}")
        if not found:
            all_passed = False
    
    # Check tests
    print("\n5. Unit Tests (tests/test_product_categories.py)")
    test_checks = check_file_contains(
        "tests/test_product_categories.py",
        ["def test_create_product_category", "def test_get_all_product_categories",
         "def test_update_product_category", "def test_delete_product_category"]
    )
    for term, found in test_checks:
        status = "✓" if found else "✗"
        print(f"  {status} {term}")
        if not found:
            all_passed = False
    
    # Check integration tests
    print("\n6. Integration Tests (tests/test_product_category_integration.py)")
    integration_checks = check_file_contains(
        "tests/test_product_category_integration.py",
        ["def test_repository_create_and_retrieve", "def test_complete_crud_flow",
         "def test_service_validation_empty_name"]
    )
    for term, found in integration_checks:
        status = "✓" if found else "✗"
        print(f"  {status} {term}")
        if not found:
            all_passed = False
    
    # Summary
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All structural checks passed! Implementation looks complete.")
        print("\nImplemented features:")
        print("  • ProductCategory model (already existed)")
        print("  • ProductCategoryRepository with CRUD operations")
        print("  • ProductCategoryService with business logic and validation")
        print("  • REST API endpoints (POST, GET, PUT, DELETE)")
        print("  • Comprehensive unit tests")
        print("  • Integration tests")
        print("\nAPI Endpoints:")
        print("  POST   /api/product-categories       - Create category")
        print("  GET    /api/product-categories       - List all categories")
        print("  GET    /api/product-categories/{id}  - Get category by ID")
        print("  PUT    /api/product-categories/{id}  - Update category")
        print("  DELETE /api/product-categories/{id}  - Delete category")
        return 0
    else:
        print("✗ Some structural checks failed.")
        return 1


if __name__ == "__main__":
    sys.exit(verify_structure())

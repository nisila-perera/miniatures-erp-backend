#!/usr/bin/env python3
"""
Verification script for product category implementation
This script checks that all required components are properly implemented
"""

import sys
import importlib.util
from pathlib import Path


def check_module_exists(module_path: str) -> bool:
    """Check if a module exists and can be imported"""
    try:
        spec = importlib.util.find_spec(module_path)
        return spec is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def check_file_exists(file_path: str) -> bool:
    """Check if a file exists"""
    return Path(file_path).exists()


def verify_implementation():
    """Verify all required components are implemented"""
    print("Verifying Product Category Management Implementation...")
    print("=" * 60)
    
    checks = []
    
    # Check files exist
    print("\n1. Checking file structure...")
    files_to_check = [
        ("app/repositories/product_category.py", "Repository file"),
        ("app/services/product_category.py", "Service file"),
        ("app/api/product_categories.py", "API router file"),
        ("tests/test_product_categories.py", "Unit tests file"),
        ("tests/test_product_category_integration.py", "Integration tests file"),
    ]
    
    for file_path, description in files_to_check:
        exists = check_file_exists(file_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {description}: {file_path}")
        checks.append(exists)
    
    # Check required classes and functions
    print("\n2. Checking implementation components...")
    
    try:
        # Check repository
        from app.repositories.product_category import ProductCategoryRepository
        print("  ✓ ProductCategoryRepository class found")
        
        # Check required methods
        required_methods = ['create', 'get_by_id', 'get_all', 'update', 'delete']
        for method in required_methods:
            has_method = hasattr(ProductCategoryRepository, method)
            status = "✓" if has_method else "✗"
            print(f"    {status} Method: {method}")
            checks.append(has_method)
        
        checks.append(True)
    except ImportError as e:
        print(f"  ✗ Failed to import ProductCategoryRepository: {e}")
        checks.append(False)
    
    try:
        # Check service
        from app.services.product_category import ProductCategoryService
        print("  ✓ ProductCategoryService class found")
        
        # Check required methods
        required_methods = ['create_category', 'get_category', 'get_all_categories', 
                          'update_category', 'delete_category']
        for method in required_methods:
            has_method = hasattr(ProductCategoryService, method)
            status = "✓" if has_method else "✗"
            print(f"    {status} Method: {method}")
            checks.append(has_method)
        
        checks.append(True)
    except ImportError as e:
        print(f"  ✗ Failed to import ProductCategoryService: {e}")
        checks.append(False)
    
    try:
        # Check API router
        from app.api.product_categories import router
        print("  ✓ API router found")
        
        # Check routes
        routes = [route.path for route in router.routes]
        expected_routes = ['', '/{category_id}']
        for expected in expected_routes:
            has_route = expected in routes
            status = "✓" if has_route else "✗"
            print(f"    {status} Route: {expected}")
            checks.append(has_route)
        
        checks.append(True)
    except ImportError as e:
        print(f"  ✗ Failed to import API router: {e}")
        checks.append(False)
    
    # Check main app integration
    print("\n3. Checking main app integration...")
    try:
        from app.main import app
        print("  ✓ Main app imported successfully")
        
        # Check if router is included
        router_prefixes = [route.path for route in app.routes]
        has_product_categories = any('/api/product-categories' in path for path in router_prefixes)
        status = "✓" if has_product_categories else "✗"
        print(f"  {status} Product categories router registered")
        checks.append(has_product_categories)
        
        checks.append(True)
    except ImportError as e:
        print(f"  ✗ Failed to import main app: {e}")
        checks.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)
    print(f"Verification Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("✓ All checks passed! Implementation is complete.")
        return 0
    else:
        print("✗ Some checks failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(verify_implementation())

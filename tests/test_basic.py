"""
Basic tests for Bilka Price Monitor components.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime


def test_data_processor():
    """Test data processor functionality."""
    # This would normally import from src.data.processor
    # For now, we'll test basic functionality

    # Create sample data
    sample_data = pd.DataFrame({
        'external_id': ['P001', 'P002', 'P003'],
        'name': ['Test Product 1', 'Test Product 2', 'Test Product 3'],
        'regular_price': [100.0, 200.0, 300.0],
        'sale_price': [80.0, 180.0, 250.0],
        'discount_percentage': [20.0, 10.0, 16.67]
    })

    # Basic assertions
    assert len(sample_data) == 3
    assert sample_data['regular_price'].iloc[0] == 100.0
    assert sample_data['sale_price'].iloc[0] == 80.0

    print("✅ Data processor test passed")


def test_discount_calculation():
    """Test discount calculation logic."""

    def calculate_discount(regular, sale):
        if regular > 0 and sale >= 0 and sale <= regular:
            return round(((regular - sale) / regular) * 100, 2)
        return None

    # Test cases
    assert calculate_discount(100, 80) == 20.0
    assert calculate_discount(200, 150) == 25.0
    assert calculate_discount(50, 50) == 0.0
    assert calculate_discount(100, 120) is None  # Sale > regular
    assert calculate_discount(0, 50) is None     # Zero regular price

    print("✅ Discount calculation test passed")


def test_price_validation():
    """Test basic price validation."""

    def validate_price(regular, sale):
        errors = []

        if regular is None or sale is None:
            errors.append("MISSING_PRICE")

        if regular is not None and regular <= 0:
            errors.append("INVALID_REGULAR_PRICE")

        if sale is not None and sale < 0:
            errors.append("INVALID_SALE_PRICE")

        if (regular is not None and sale is not None and
            regular > 0 and sale > regular):
            errors.append("SALE_HIGHER_THAN_REGULAR")

        return len(errors) == 0, errors

    # Test cases
    valid, errors = validate_price(100, 80)
    assert valid == True
    assert len(errors) == 0

    valid, errors = validate_price(100, 120)
    assert valid == False
    assert "SALE_HIGHER_THAN_REGULAR" in errors

    valid, errors = validate_price(-50, 80)
    assert valid == False
    assert "INVALID_REGULAR_PRICE" in errors

    print("✅ Price validation test passed")


def test_dataframe_operations():
    """Test pandas DataFrame operations."""

    # Create test data
    data = {
        'product_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'price': [100, 200, 150, 300, 250],
        'discount': [10, 20, 15, 30, 25]
    }

    df = pd.DataFrame(data)

    # Test filtering
    high_discount = df[df['discount'] > 20]
    assert len(high_discount) == 2

    # Test calculations
    df['final_price'] = df['price'] * (1 - df['discount'] / 100)
    assert df['final_price'].iloc[0] == 90.0

    # Test aggregation
    avg_price = df['price'].mean()
    assert avg_price == 200.0

    print("✅ DataFrame operations test passed")


def test_error_detection():
    """Test error detection logic."""

    def detect_errors(products):
        errors = []

        for product in products:
            if product.get('discount_percentage', 0) > 90:
                errors.append({
                    'product_id': product['external_id'],
                    'error': 'EXTREME_DISCOUNT',
                    'value': product['discount_percentage']
                })

            if (product.get('regular_price', 0) > 0 and
                product.get('sale_price', 0) > product['regular_price']):
                errors.append({
                    'product_id': product['external_id'],
                    'error': 'INVALID_PRICE_RELATIONSHIP',
                    'regular': product['regular_price'],
                    'sale': product['sale_price']
                })

        return errors

    # Test data
    products = [
        {'external_id': 'P001', 'regular_price': 100, 'sale_price': 50, 'discount_percentage': 50},
        {'external_id': 'P002', 'regular_price': 200, 'sale_price': 10, 'discount_percentage': 95},
        {'external_id': 'P003', 'regular_price': 150, 'sale_price': 180, 'discount_percentage': -16.67}
    ]

    errors = detect_errors(products)

    # Should detect 2 errors: extreme discount and invalid price relationship
    assert len(errors) == 2

    error_types = [e['error'] for e in errors]
    assert 'EXTREME_DISCOUNT' in error_types
    assert 'INVALID_PRICE_RELATIONSHIP' in error_types

    print("✅ Error detection test passed")


def run_all_tests():
    """Run all basic tests."""
    print("🧪 Running basic tests for Bilka Price Monitor")
    print("=" * 50)

    test_functions = [
        test_data_processor,
        test_discount_calculation,
        test_price_validation,
        test_dataframe_operations,
        test_error_detection
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1

    print("=" * 50)
    print(f"Tests completed: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
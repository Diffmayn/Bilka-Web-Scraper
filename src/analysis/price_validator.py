"""
Price Validator for detecting pricing anomalies and errors
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Price validation report"""
    total_products: int
    valid_products: int
    invalid_products: int
    errors: List[Dict]
    warnings: List[Dict]
    validation_passed: bool


class PriceValidator:
    """Validates product pricing data for errors and anomalies"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.max_price = self.config.get('max_price', 100000)  # DKK
        self.min_price = self.config.get('min_price', 0.01)
        self.max_discount = self.config.get('max_discount', 95)

    def validate(self, products_df: pd.DataFrame) -> ValidationReport:
        """
        Validate product pricing data
        
        Args:
            products_df: DataFrame with product data
            
        Returns:
            ValidationReport with validation results
        """
        if products_df.empty:
            return self._empty_report()

        total_products = len(products_df)
        errors = []
        warnings = []

        for idx, row in products_df.iterrows():
            product_errors = self._validate_product(row)
            if product_errors:
                for error in product_errors:
                    if error['severity'] in ['CRITICAL', 'HIGH']:
                        errors.append(error)
                    else:
                        warnings.append(error)

        invalid_products = len(set(e['name'] for e in errors))
        valid_products = total_products - invalid_products
        validation_passed = len(errors) == 0

        report = ValidationReport(
            total_products=total_products,
            valid_products=valid_products,
            invalid_products=invalid_products,
            errors=errors,
            warnings=warnings,
            validation_passed=validation_passed
        )

        logger.info(f"Validation complete: {valid_products}/{total_products} valid products")
        return report

    def _validate_product(self, row: pd.Series) -> List[Dict]:
        """Validate a single product"""
        errors = []
        name = row.get('name', 'Unknown')
        current = row.get('current_price')
        original = row.get('original_price')
        discount = row.get('discount_percentage')

        # Validation 1: Missing data
        if not name or not current:
            errors.append({
                'name': name,
                'type': 'MISSING_DATA',
                'severity': 'HIGH',
                'description': 'Missing required product data (name or price)'
            })

        # Validation 2: Price range
        if current is not None:
            if current < self.min_price:
                errors.append({
                    'name': name,
                    'type': 'PRICE_TOO_LOW',
                    'severity': 'HIGH',
                    'description': f'Price {current:.2f} below minimum {self.min_price}',
                    'current_price': current
                })
            elif current > self.max_price:
                errors.append({
                    'name': name,
                    'type': 'PRICE_TOO_HIGH',
                    'severity': 'MEDIUM',
                    'description': f'Price {current:.2f} exceeds maximum {self.max_price}',
                    'current_price': current
                })

        # Validation 3: Negative prices
        if current is not None and current < 0:
            errors.append({
                'name': name,
                'type': 'NEGATIVE_PRICE',
                'severity': 'CRITICAL',
                'description': f'Negative price: {current:.2f}',
                'current_price': current
            })

        # Validation 4: Price inversion
        if current and original and current > original:
            errors.append({
                'name': name,
                'type': 'PRICE_INVERSION',
                'severity': 'HIGH',
                'description': f'Current price ({current:.2f}) > Original ({original:.2f})',
                'current_price': current,
                'original_price': original
            })

        # Validation 5: Discount range
        if discount is not None:
            if discount < 0:
                errors.append({
                    'name': name,
                    'type': 'NEGATIVE_DISCOUNT',
                    'severity': 'HIGH',
                    'description': f'Negative discount: {discount:.1f}%',
                    'discount_percentage': discount
                })
            elif discount > self.max_discount:
                errors.append({
                    'name': name,
                    'type': 'EXCESSIVE_DISCOUNT',
                    'severity': 'MEDIUM',
                    'description': f'Discount {discount:.1f}% exceeds maximum {self.max_discount}%',
                    'discount_percentage': discount
                })

        # Validation 6: Discount calculation
        if current and original and discount:
            calculated_discount = ((original - current) / original) * 100 if original > 0 else 0
            if abs(calculated_discount - discount) > 5:  # 5% tolerance
                errors.append({
                    'name': name,
                    'type': 'DISCOUNT_CALCULATION_ERROR',
                    'severity': 'MEDIUM',
                    'description': f'Discount mismatch: claimed {discount:.1f}%, calculated {calculated_discount:.1f}%',
                    'claimed_discount': discount,
                    'calculated_discount': calculated_discount
                })

        return errors

    def _empty_report(self) -> ValidationReport:
        """Return empty validation report"""
        return ValidationReport(
            total_products=0,
            valid_products=0,
            invalid_products=0,
            errors=[],
            warnings=[],
            validation_passed=True
        )


def validate_product_prices(products_df: pd.DataFrame, config: Optional[Dict] = None) -> ValidationReport:
    """
    Convenience function to validate product prices
    
    Args:
        products_df: DataFrame with product data
        config: Optional configuration dictionary
        
    Returns:
        ValidationReport object
    """
    validator = PriceValidator(config)
    return validator.validate(products_df)

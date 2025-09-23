"""
Price Validator for Bilka Price Monitor

Validates pricing data and detects anomalies using various validation methods.
Provides comprehensive price validation and error detection.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger

from .discount_analyzer import DiscountAnalyzer


@dataclass
class ValidationResult:
    """Data class for validation results."""
    is_valid: bool
    error_code: Optional[str]
    error_message: Optional[str]
    severity: str
    suggestions: List[str]


@dataclass
class PriceValidationReport:
    """Data class for comprehensive price validation report."""
    total_products: int
    valid_products: int
    invalid_products: int
    validation_errors: List[Dict[str, Any]]
    anomaly_summary: Dict[str, int]
    recommendations: List[str]


class PriceValidator:
    """
    Comprehensive price validator for detecting pricing errors and anomalies.

    Uses multiple validation methods including statistical analysis,
    business rule validation, and historical comparison.
    """

    def __init__(self, historical_data: Optional[pd.DataFrame] = None):
        """
        Initialize the price validator.

        Args:
            historical_data: Historical pricing data for comparison
        """
        self.historical_data = historical_data
        self.discount_analyzer = DiscountAnalyzer(historical_data)

        # Validation rules
        self.rules = {
            'max_price': 100000,  # Maximum expected price in DKK
            'min_price': 0.01,    # Minimum expected price in DKK
            'max_discount': 95,   # Maximum expected discount percentage
            'price_deviation_threshold': 0.5,  # 50% deviation threshold
            'statistical_outlier_threshold': 3.0  # Z-score threshold
        }

        logger.info("Price validator initialized")

    def validate_product_price(self, regular_price: Optional[float],
                              sale_price: Optional[float],
                              discount_percentage: Optional[float] = None) -> ValidationResult:
        """
        Validate pricing data for a single product.

        Args:
            regular_price: Regular price
            sale_price: Sale price
            discount_percentage: Discount percentage

        Returns:
            ValidationResult object
        """
        errors = []
        suggestions = []

        # Rule 1: Check for missing prices
        if regular_price is None and sale_price is None:
            errors.append("MISSING_PRICES")
            suggestions.append("Product must have at least one price (regular or sale)")

        # Rule 2: Validate price ranges
        for price, price_type in [(regular_price, 'regular'), (sale_price, 'sale')]:
            if price is not None:
                if price < self.rules['min_price']:
                    errors.append(f"NEGATIVE_{price_type.upper()}_PRICE")
                    suggestions.append(f"{price_type.title()} price cannot be negative or zero")
                elif price > self.rules['max_price']:
                    errors.append(f"EXCESSIVE_{price_type.upper()}_PRICE")
                    suggestions.append(f"{price_type.title()} price seems unusually high - please verify")

        # Rule 3: Validate price relationship
        if regular_price is not None and sale_price is not None:
            if sale_price > regular_price:
                errors.append("INVALID_PRICE_RELATIONSHIP")
                suggestions.append("Sale price cannot be higher than regular price")
            elif regular_price == sale_price:
                suggestions.append("Regular and sale prices are identical - consider if discount is needed")

        # Rule 4: Validate discount percentage
        if discount_percentage is not None:
            if discount_percentage < 0:
                errors.append("NEGATIVE_DISCOUNT")
                suggestions.append("Discount percentage cannot be negative")
            elif discount_percentage > self.rules['max_discount']:
                errors.append("EXCESSIVE_DISCOUNT")
                suggestions.append(f"Discount percentage over {self.rules['max_discount']}% seems unusual")

        # Rule 5: Cross-validate calculated vs provided discount
        if (regular_price is not None and sale_price is not None and
            discount_percentage is not None and regular_price > 0):

            calculated_discount = ((regular_price - sale_price) / regular_price) * 100
            if abs(calculated_discount - discount_percentage) > 1.0:  # 1% tolerance
                errors.append("DISCOUNT_MISMATCH")
                suggestions.append(".1f")

        # Determine overall result
        if errors:
            severity = self._determine_severity(errors)
            return ValidationResult(
                is_valid=False,
                error_code=errors[0],  # Primary error
                error_message=self._get_error_message(errors[0]),
                severity=severity,
                suggestions=suggestions
            )
        else:
            return ValidationResult(
                is_valid=True,
                error_code=None,
                error_message=None,
                severity='low',
                suggestions=suggestions
            )

    def validate_product_dataset(self, df: pd.DataFrame) -> PriceValidationReport:
        """
        Validate an entire dataset of product prices.

        Args:
            df: DataFrame with product pricing data

        Returns:
            PriceValidationReport object
        """
        total_products = len(df)
        valid_products = 0
        invalid_products = 0
        validation_errors = []
        anomaly_summary = {}

        # Validate each product
        for idx, product in df.iterrows():
            result = self.validate_product_price(
                product.get('regular_price'),
                product.get('sale_price'),
                product.get('discount_percentage')
            )

            if result.is_valid:
                valid_products += 1
            else:
                invalid_products += 1

                # Track error types
                error_type = result.error_code or 'UNKNOWN'
                anomaly_summary[error_type] = anomaly_summary.get(error_type, 0) + 1

                validation_errors.append({
                    'product_id': product.get('external_id'),
                    'name': product.get('name'),
                    'error_code': result.error_code,
                    'error_message': result.error_message,
                    'severity': result.severity,
                    'suggestions': result.suggestions,
                    'regular_price': product.get('regular_price'),
                    'sale_price': product.get('sale_price'),
                    'discount_percentage': product.get('discount_percentage')
                })

        # Generate recommendations
        recommendations = self._generate_validation_recommendations(
            total_products, invalid_products, anomaly_summary
        )

        return PriceValidationReport(
            total_products=total_products,
            valid_products=valid_products,
            invalid_products=invalid_products,
            validation_errors=validation_errors,
            anomaly_summary=anomaly_summary,
            recommendations=recommendations
        )

    def detect_statistical_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect statistical anomalies in pricing data.

        Args:
            df: DataFrame with pricing data

        Returns:
            List of anomaly dictionaries
        """
        anomalies = []

        # Analyze regular prices
        if 'regular_price' in df.columns:
            price_data = df['regular_price'].dropna()
            if len(price_data) > 10:
                price_anomalies = self._detect_outliers(price_data, 'regular_price')
                anomalies.extend(price_anomalies)

        # Analyze sale prices
        if 'sale_price' in df.columns:
            sale_data = df['sale_price'].dropna()
            if len(sale_data) > 10:
                sale_anomalies = self._detect_outliers(sale_data, 'sale_price')
                anomalies.extend(sale_anomalies)

        # Analyze discount percentages
        if 'discount_percentage' in df.columns:
            discount_data = df['discount_percentage'].dropna()
            if len(discount_data) > 10:
                discount_anomalies = self._detect_outliers(discount_data, 'discount_percentage')
                anomalies.extend(discount_anomalies)

        logger.info(f"Detected {len(anomalies)} statistical anomalies")
        return anomalies

    def _detect_outliers(self, data: pd.Series, column_name: str) -> List[Dict[str, Any]]:
        """
        Detect outliers in a data series using statistical methods.

        Args:
            data: Data series to analyze
            column_name: Name of the column being analyzed

        Returns:
            List of outlier dictionaries
        """
        anomalies = []

        # Calculate z-scores
        z_scores = np.abs((data - data.mean()) / data.std())

        # Find outliers
        outlier_mask = z_scores > self.rules['statistical_outlier_threshold']
        outlier_indices = data[outlier_mask].index

        for idx in outlier_indices:
            product_data = data.index[idx] if hasattr(data.index, '__getitem__') else idx

            # Get product information if available
            product_info = {}
            if isinstance(data.index, pd.MultiIndex) or hasattr(data, 'name'):
                # Try to get product details from the DataFrame
                try:
                    product_row = data.index[idx] if hasattr(data.index, '__getitem__') else None
                    if product_row is not None:
                        product_info = {
                            'value': data.loc[product_row],
                            'z_score': z_scores.loc[product_row]
                        }
                except:
                    pass

            anomalies.append({
                'column': column_name,
                'value': data.loc[idx],
                'z_score': z_scores.loc[idx],
                'anomaly_type': 'statistical_outlier',
                'severity': 'medium',
                'description': f"{column_name} is {z_scores.loc[idx]:.2f} standard deviations from mean"
            })

        return anomalies

    def validate_historical_consistency(self, current_df: pd.DataFrame,
                                       historical_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Validate pricing consistency with historical data.

        Args:
            current_df: Current pricing data
            historical_df: Historical pricing data

        Returns:
            List of consistency issue dictionaries
        """
        issues = []

        if historical_df is None or historical_df.empty:
            return issues

        # Merge datasets
        merged_df = current_df.merge(
            historical_df,
            on='external_id',
            suffixes=('_current', '_historical'),
            how='inner'
        )

        # Check for significant price changes
        price_columns = ['regular_price', 'sale_price']
        for price_col in price_columns:
            current_col = f"{price_col}_current"
            historical_col = f"{price_col}_historical"

            if current_col in merged_df.columns and historical_col in merged_df.columns:
                # Calculate percentage change
                merged_df[f"{price_col}_change_pct"] = (
                    (merged_df[current_col] - merged_df[historical_col]) /
                    merged_df[historical_col] * 100
                ).abs()

                # Find significant changes
                significant_changes = merged_df[
                    merged_df[f"{price_col}_change_pct"] > (self.rules['price_deviation_threshold'] * 100)
                ]

                for _, product in significant_changes.iterrows():
                    issues.append({
                        'product_id': product['external_id'],
                        'name': product['name_current'],
                        'issue_type': 'significant_price_change',
                        'severity': 'high',
                        'description': f"{price_col} changed by {product[f'{price_col}_change_pct']:.1f}%",
                        'current_value': product[current_col],
                        'historical_value': product[historical_col],
                        'change_percentage': product[f"{price_col}_change_pct"]
                    })

        logger.info(f"Found {len(issues)} historical consistency issues")
        return issues

    def validate_business_rules(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Validate business-specific pricing rules.

        Args:
            df: DataFrame with product data

        Returns:
            List of business rule violation dictionaries
        """
        violations = []

        # Rule 1: Products should have reasonable discount ranges
        discount_violations = df[
            (df['discount_percentage'].notna()) &
            ((df['discount_percentage'] < 0) | (df['discount_percentage'] > 95))
        ]

        for _, product in discount_violations.iterrows():
            violations.append({
                'product_id': product.get('external_id'),
                'name': product.get('name'),
                'rule_type': 'discount_range',
                'severity': 'high',
                'description': f"Discount {product['discount_percentage']}% outside acceptable range (0-95%)",
                'current_value': product['discount_percentage']
            })

        # Rule 2: High-value items shouldn't have extreme discounts
        high_value_extreme_discounts = df[
            (df['regular_price'] > 1000) &
            (df['discount_percentage'].notna()) &
            (df['discount_percentage'] > 80)
        ]

        for _, product in high_value_extreme_discounts.iterrows():
            violations.append({
                'product_id': product.get('external_id'),
                'name': product.get('name'),
                'rule_type': 'high_value_extreme_discount',
                'severity': 'medium',
                'description': f"High-value item (DKK {product['regular_price']}) with extreme discount ({product['discount_percentage']}%)",
                'regular_price': product['regular_price'],
                'discount_percentage': product['discount_percentage']
            })

        # Rule 3: Check for round number discounts (potential errors)
        round_discounts = df[
            (df['discount_percentage'].notna()) &
            (df['discount_percentage'] % 5 == 0) &
            (df['discount_percentage'] > 0)
        ]

        if len(round_discounts) > len(df) * 0.3:  # More than 30% round discounts
            violations.append({
                'product_id': 'SYSTEM',
                'name': 'System-wide check',
                'rule_type': 'too_many_round_discounts',
                'severity': 'low',
                'description': f"{len(round_discounts)} products have round number discounts - may indicate data entry patterns"
            })

        logger.info(f"Found {len(violations)} business rule violations")
        return violations

    def _determine_severity(self, errors: List[str]) -> str:
        """Determine overall severity from error codes."""
        critical_errors = ['MISSING_PRICES', 'NEGATIVE_REGULAR_PRICE', 'NEGATIVE_SALE_PRICE']
        high_errors = ['INVALID_PRICE_RELATIONSHIP', 'EXCESSIVE_REGULAR_PRICE', 'EXCESSIVE_SALE_PRICE']

        if any(error in critical_errors for error in errors):
            return 'critical'
        elif any(error in high_errors for error in errors):
            return 'high'
        else:
            return 'medium'

    def _get_error_message(self, error_code: str) -> str:
        """Get human-readable error message for error code."""
        messages = {
            'MISSING_PRICES': 'Product is missing pricing information',
            'NEGATIVE_REGULAR_PRICE': 'Regular price cannot be negative or zero',
            'NEGATIVE_SALE_PRICE': 'Sale price cannot be negative or zero',
            'EXCESSIVE_REGULAR_PRICE': 'Regular price seems unusually high',
            'EXCESSIVE_SALE_PRICE': 'Sale price seems unusually high',
            'INVALID_PRICE_RELATIONSHIP': 'Sale price cannot be higher than regular price',
            'NEGATIVE_DISCOUNT': 'Discount percentage cannot be negative',
            'EXCESSIVE_DISCOUNT': 'Discount percentage seems unusually high',
            'DISCOUNT_MISMATCH': 'Calculated discount does not match provided discount'
        }
        return messages.get(error_code, f'Unknown error: {error_code}')

    def _generate_validation_recommendations(self, total: int, invalid: int,
                                           anomaly_summary: Dict[str, int]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        error_rate = invalid / total if total > 0 else 0

        if error_rate > 0.5:
            recommendations.append(
                ".1f"
            )
        elif error_rate > 0.2:
            recommendations.append(
                ".1f"
            )

        # Specific recommendations based on error types
        if anomaly_summary.get('MISSING_PRICES', 0) > 0:
            recommendations.append(
                f"Address {anomaly_summary['MISSING_PRICES']} products missing price data"
            )

        if anomaly_summary.get('INVALID_PRICE_RELATIONSHIP', 0) > 0:
            recommendations.append(
                f"Fix {anomaly_summary['INVALID_PRICE_RELATIONSHIP']} products with incorrect price relationships"
            )

        if anomaly_summary.get('EXCESSIVE_DISCOUNT', 0) > 0:
            recommendations.append(
                f"Review {anomaly_summary['EXCESSIVE_DISCOUNT']} products with unusually high discounts"
            )

        return recommendations if recommendations else ["Data validation completed successfully"]

    def generate_validation_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.

        Args:
            df: DataFrame with product data

        Returns:
            Dictionary containing the validation report
        """
        # Basic validation
        validation_report = self.validate_product_dataset(df)

        # Statistical anomalies
        statistical_anomalies = self.detect_statistical_anomalies(df)

        # Historical consistency (if available)
        historical_issues = []
        if self.historical_data is not None:
            historical_issues = self.validate_historical_consistency(df, self.historical_data)

        # Business rule violations
        business_violations = self.validate_business_rules(df)

        # Discount analysis
        discount_analysis = self.discount_analyzer.analyze_discounts(df)

        report = {
            'summary': {
                'total_products': validation_report.total_products,
                'valid_products': validation_report.valid_products,
                'invalid_products': validation_report.invalid_products,
                'validation_rate': round(validation_report.valid_products / validation_report.total_products * 100, 2)
            },
            'validation_errors': {
                'total_errors': len(validation_report.validation_errors),
                'error_breakdown': validation_report.anomaly_summary,
                'top_errors': validation_report.validation_errors[:10]
            },
            'anomalies': {
                'statistical': len(statistical_anomalies),
                'historical': len(historical_issues),
                'business_rules': len(business_violations)
            },
            'discount_analysis': {
                'products_with_discount': discount_analysis.products_with_discount,
                'average_discount': discount_analysis.average_discount,
                'high_discount_products': len(discount_analysis.high_discount_products)
            },
            'recommendations': validation_report.recommendations,
            'generated_at': datetime.now().isoformat()
        }

        return report


# Convenience functions
def validate_product_prices(df: pd.DataFrame) -> PriceValidationReport:
    """
    Convenience function to validate product prices.

    Args:
        df: DataFrame with product data

    Returns:
        PriceValidationReport object
    """
    validator = PriceValidator()
    return validator.validate_product_dataset(df)


def detect_price_anomalies(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convenience function to detect price anomalies.

    Args:
        df: DataFrame with product data

    Returns:
        List of anomaly dictionaries
    """
    validator = PriceValidator()
    return validator.detect_statistical_anomalies(df)
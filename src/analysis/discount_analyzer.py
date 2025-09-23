"""
Discount Analyzer for Bilka Price Monitor

Analyzes pricing data to detect discounts, anomalies, and potential errors.
Provides comprehensive discount analysis and error detection algorithms.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger

from src.data.processor import DataProcessor


@dataclass
class DiscountAnalysis:
    """Data class for discount analysis results."""
    total_products: int
    products_with_discount: int
    average_discount: float
    max_discount: float
    discount_distribution: Dict[str, int]
    potential_errors: List[Dict[str, Any]]
    high_discount_products: List[Dict[str, Any]]


@dataclass
class PriceAnomaly:
    """Data class for price anomalies."""
    product_id: str
    product_name: str
    anomaly_type: str
    severity: str
    description: str
    regular_price: Optional[float]
    sale_price: Optional[float]
    discount_percentage: Optional[float]
    detected_at: datetime


class DiscountAnalyzer:
    """
    Advanced discount analyzer for detecting pricing anomalies and errors.

    Provides multiple analysis methods including statistical analysis,
    historical comparison, and rule-based error detection.
    """

    def __init__(self, historical_data: Optional[pd.DataFrame] = None):
        """
        Initialize the discount analyzer.

        Args:
            historical_data: Historical pricing data for comparison
        """
        self.historical_data = historical_data
        self.processor = DataProcessor()

        # Analysis thresholds
        self.high_discount_threshold = 75.0
        self.critical_discount_threshold = 90.0
        self.price_error_margin = 0.05  # 5% tolerance

        logger.info("Discount analyzer initialized")

    def analyze_discounts(self, df: pd.DataFrame) -> DiscountAnalysis:
        """
        Perform comprehensive discount analysis on product data.

        Args:
            df: DataFrame with product pricing data

        Returns:
            DiscountAnalysis object with analysis results
        """
        # Ensure we have the necessary columns
        required_columns = ['external_id', 'name', 'regular_price', 'sale_price', 'discount_percentage']
        for col in required_columns:
            if col not in df.columns:
                df[col] = None

        # Calculate discount metrics
        df = self._calculate_discount_metrics(df)

        # Basic statistics
        total_products = len(df)
        products_with_discount = df['has_discount'].sum()
        average_discount = df.loc[df['has_discount'], 'discount_percentage'].mean()
        max_discount = df['discount_percentage'].max()

        # Discount distribution
        discount_bins = [0, 10, 25, 50, 75, 90, 100]
        discount_labels = ['0-10%', '10-25%', '25-50%', '50-75%', '75-90%', '90-100%']
        df['discount_range'] = pd.cut(df['discount_percentage'], bins=discount_bins, labels=discount_labels)
        discount_distribution = df['discount_range'].value_counts().to_dict()

        # Detect potential errors
        potential_errors = self._detect_potential_errors(df)

        # High discount products
        high_discount_products = self._get_high_discount_products(df)

        return DiscountAnalysis(
            total_products=total_products,
            products_with_discount=int(products_with_discount),
            average_discount=round(average_discount, 2) if not np.isnan(average_discount) else 0.0,
            max_discount=round(max_discount, 2) if not np.isnan(max_discount) else 0.0,
            discount_distribution=discount_distribution,
            potential_errors=potential_errors,
            high_discount_products=high_discount_products
        )

    def _calculate_discount_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate discount-related metrics for the dataset.

        Args:
            df: DataFrame with pricing data

        Returns:
            DataFrame with additional discount metrics
        """
        df = df.copy()

        # Calculate discount percentage if not present
        mask = (
            df['discount_percentage'].isna() &
            df['regular_price'].notna() &
            df['sale_price'].notna() &
            (df['regular_price'] > 0)
        )

        df.loc[mask, 'discount_percentage'] = (
            (df.loc[mask, 'regular_price'] - df.loc[mask, 'sale_price']) /
            df.loc[mask, 'regular_price'] * 100
        ).round(2)

        # Flag products with discounts
        df['has_discount'] = (
            df['discount_percentage'].notna() &
            (df['discount_percentage'] > 0)
        )

        # Calculate discount severity
        conditions = [
            df['discount_percentage'].isna(),
            df['discount_percentage'] < 25,
            df['discount_percentage'] < 50,
            df['discount_percentage'] < 75,
            df['discount_percentage'] < 90,
            df['discount_percentage'] >= 90
        ]
        choices = ['No Discount', 'Low', 'Medium', 'High', 'Very High', 'Extreme']
        df['discount_severity'] = np.select(conditions, choices, default='Unknown')

        return df

    def _detect_potential_errors(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect potential pricing errors using multiple methods.

        Args:
            df: DataFrame with pricing data

        Returns:
            List of potential error dictionaries
        """
        errors = []

        # Method 1: Extreme discount detection
        extreme_discounts = df[
            (df['discount_percentage'] > self.critical_discount_threshold) &
            (df['discount_percentage'].notna())
        ]

        for _, product in extreme_discounts.iterrows():
            errors.append({
                'product_id': product['external_id'],
                'name': product['name'],
                'error_type': 'extreme_discount',
                'severity': 'critical',
                'description': f"Extreme discount: {product['discount_percentage']:.1f}%",
                'regular_price': product['regular_price'],
                'sale_price': product['sale_price'],
                'discount_percentage': product['discount_percentage']
            })

        # Method 2: Invalid price relationships
        invalid_prices = df[
            (df['regular_price'].notna()) &
            (df['sale_price'].notna()) &
            (df['sale_price'] > df['regular_price'])
        ]

        for _, product in invalid_prices.iterrows():
            errors.append({
                'product_id': product['external_id'],
                'name': product['name'],
                'error_type': 'invalid_price_relationship',
                'severity': 'high',
                'description': f"Sale price ({product['sale_price']}) > Regular price ({product['regular_price']})",
                'regular_price': product['regular_price'],
                'sale_price': product['sale_price'],
                'discount_percentage': product['discount_percentage']
            })

        # Method 3: Negative prices
        negative_prices = df[
            ((df['regular_price'] < 0) & df['regular_price'].notna()) |
            ((df['sale_price'] < 0) & df['sale_price'].notna())
        ]

        for _, product in negative_prices.iterrows():
            price_type = 'regular' if product['regular_price'] < 0 else 'sale'
            errors.append({
                'product_id': product['external_id'],
                'name': product['name'],
                'error_type': 'negative_price',
                'severity': 'critical',
                'description': f"Negative {price_type} price: {product[f'{price_type}_price']}",
                'regular_price': product['regular_price'],
                'sale_price': product['sale_price'],
                'discount_percentage': product['discount_percentage']
            })

        # Method 4: Missing price data
        missing_prices = df[
            df['regular_price'].isna() & df['sale_price'].isna()
        ]

        for _, product in missing_prices.iterrows():
            errors.append({
                'product_id': product['external_id'],
                'name': product['name'],
                'error_type': 'missing_price_data',
                'severity': 'medium',
                'description': "Missing both regular and sale price data",
                'regular_price': product['regular_price'],
                'sale_price': product['sale_price'],
                'discount_percentage': product['discount_percentage']
            })

        # Method 5: Historical price deviation (if historical data available)
        if self.historical_data is not None:
            historical_errors = self._detect_historical_anomalies(df)
            errors.extend(historical_errors)

        logger.info(f"Detected {len(errors)} potential pricing errors")
        return errors

    def _detect_historical_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect anomalies by comparing with historical data.

        Args:
            df: Current pricing data

        Returns:
            List of historical anomaly dictionaries
        """
        errors = []

        if self.historical_data is None or self.historical_data.empty:
            return errors

        # Merge with historical data
        historical_avg = self.historical_data.groupby('external_id')['regular_price'].mean().reset_index()
        historical_avg.columns = ['external_id', 'historical_avg_price']

        merged_df = df.merge(historical_avg, on='external_id', how='left')

        # Find significant price deviations
        deviation_threshold = 0.5  # 50% deviation
        significant_deviations = merged_df[
            (merged_df['historical_avg_price'].notna()) &
            (merged_df['regular_price'].notna()) &
            (
                (merged_df['regular_price'] > merged_df['historical_avg_price'] * (1 + deviation_threshold)) |
                (merged_df['regular_price'] < merged_df['historical_avg_price'] * (1 - deviation_threshold))
            )
        ]

        for _, product in significant_deviations.iterrows():
            deviation_pct = (
                (product['regular_price'] - product['historical_avg_price']) /
                product['historical_avg_price'] * 100
            )

            errors.append({
                'product_id': product['external_id'],
                'name': product['name'],
                'error_type': 'historical_deviation',
                'severity': 'high',
                'description': f"Price deviates {deviation_pct:.1f}% from historical average",
                'regular_price': product['regular_price'],
                'sale_price': product['sale_price'],
                'discount_percentage': product['discount_percentage'],
                'historical_avg': product['historical_avg_price']
            })

        return errors

    def _get_high_discount_products(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Get products with high discounts for review.

        Args:
            df: DataFrame with pricing data

        Returns:
            List of high discount product dictionaries
        """
        high_discount_df = df[
            (df['discount_percentage'] >= self.high_discount_threshold) &
            (df['discount_percentage'].notna())
        ].copy()

        high_discount_df = high_discount_df.sort_values('discount_percentage', ascending=False)

        high_discount_products = []
        for _, product in high_discount_df.iterrows():
            high_discount_products.append({
                'product_id': product['external_id'],
                'name': product['name'],
                'category': product.get('category'),
                'regular_price': product['regular_price'],
                'sale_price': product['sale_price'],
                'discount_percentage': product['discount_percentage'],
                'discount_severity': product['discount_severity']
            })

        return high_discount_products

    def detect_price_anomalies_advanced(self, df: pd.DataFrame) -> List[PriceAnomaly]:
        """
        Advanced anomaly detection using statistical methods.

        Args:
            df: DataFrame with pricing data

        Returns:
            List of PriceAnomaly objects
        """
        anomalies = []

        # Statistical analysis for discount percentages
        if 'discount_percentage' in df.columns:
            discount_data = df['discount_percentage'].dropna()

            if len(discount_data) > 10:  # Need minimum data for statistical analysis
                # Calculate z-scores
                z_scores = np.abs((discount_data - discount_data.mean()) / discount_data.std())

                # Find outliers (z-score > 3)
                outlier_indices = z_scores[z_scores > 3].index

                for idx in outlier_indices:
                    product = df.loc[idx]
                    anomaly = PriceAnomaly(
                        product_id=product['external_id'],
                        product_name=product['name'],
                        anomaly_type='statistical_outlier',
                        severity='high',
                        description=f"Discount percentage is statistical outlier (z-score: {z_scores[idx]:.2f})",
                        regular_price=product.get('regular_price'),
                        sale_price=product.get('sale_price'),
                        discount_percentage=product['discount_percentage'],
                        detected_at=datetime.now()
                    )
                    anomalies.append(anomaly)

        # Price ratio analysis
        price_ratios = df[
            (df['regular_price'].notna()) &
            (df['sale_price'].notna()) &
            (df['regular_price'] > 0)
        ]

        if not price_ratios.empty:
            price_ratios['price_ratio'] = price_ratios['sale_price'] / price_ratios['regular_price']

            # Find unusual price ratios
            ratio_mean = price_ratios['price_ratio'].mean()
            ratio_std = price_ratios['price_ratio'].std()

            unusual_ratios = price_ratios[
                np.abs(price_ratios['price_ratio'] - ratio_mean) > 3 * ratio_std
            ]

            for _, product in unusual_ratios.iterrows():
                anomaly = PriceAnomaly(
                    product_id=product['external_id'],
                    product_name=product['name'],
                    anomaly_type='unusual_price_ratio',
                    severity='medium',
                    description=f"Unusual price ratio: {product['price_ratio']:.3f} (mean: {ratio_mean:.3f})",
                    regular_price=product['regular_price'],
                    sale_price=product['sale_price'],
                    discount_percentage=product['discount_percentage'],
                    detected_at=datetime.now()
                )
                anomalies.append(anomaly)

        logger.info(f"Advanced analysis detected {len(anomalies)} statistical anomalies")
        return anomalies

    def generate_discount_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a comprehensive discount analysis report.

        Args:
            df: DataFrame with pricing data

        Returns:
            Dictionary containing the analysis report
        """
        analysis = self.analyze_discounts(df)

        # Additional statistics
        df_with_metrics = self._calculate_discount_metrics(df)

        report = {
            'summary': {
                'total_products': analysis.total_products,
                'products_with_discount': analysis.products_with_discount,
                'discount_rate': round(analysis.products_with_discount / analysis.total_products * 100, 2),
                'average_discount': analysis.average_discount,
                'max_discount': analysis.max_discount
            },
            'distribution': analysis.discount_distribution,
            'errors': {
                'total_errors': len(analysis.potential_errors),
                'error_breakdown': self._categorize_errors(analysis.potential_errors),
                'error_details': analysis.potential_errors[:10]  # Top 10 errors
            },
            'high_discount_products': analysis.high_discount_products[:20],  # Top 20
            'recommendations': self._generate_recommendations(analysis),
            'generated_at': datetime.now().isoformat()
        }

        return report

    def _categorize_errors(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize errors by type."""
        categories = {}
        for error in errors:
            error_type = error.get('error_type', 'unknown')
            categories[error_type] = categories.get(error_type, 0) + 1
        return categories

    def _generate_recommendations(self, analysis: DiscountAnalysis) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []

        # Error-based recommendations
        if len(analysis.potential_errors) > 0:
            recommendations.append(
                f"Review {len(analysis.potential_errors)} products with potential pricing errors"
            )

        # High discount recommendations
        high_discount_count = len(analysis.high_discount_products)
        if high_discount_count > 0:
            recommendations.append(
                f"Verify {high_discount_count} products with discounts over {self.high_discount_threshold}%"
            )

        # Discount distribution recommendations
        if analysis.discount_distribution.get('90-100%', 0) > analysis.total_products * 0.1:
            recommendations.append(
                "High proportion of extreme discounts detected - consider reviewing pricing strategy"
            )

        # General recommendations
        if analysis.products_with_discount / analysis.total_products < 0.1:
            recommendations.append(
                "Low discount rate detected - consider if sales data is being captured correctly"
            )

        return recommendations if recommendations else ["No specific recommendations at this time"]

    def compare_with_historical(self, current_df: pd.DataFrame,
                               historical_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compare current data with historical data.

        Args:
            current_df: Current pricing data
            historical_df: Historical pricing data

        Returns:
            Dictionary with comparison results
        """
        comparison = {
            'price_changes': [],
            'new_products': [],
            'discontinued_products': [],
            'discount_changes': []
        }

        # Find price changes
        merged_prices = current_df.merge(
            historical_df,
            on='external_id',
            suffixes=('_current', '_historical'),
            how='inner'
        )

        # Price changes
        price_changes = merged_prices[
            abs(merged_prices['regular_price_current'] - merged_prices['regular_price_historical']) >
            merged_prices['regular_price_historical'] * 0.05  # 5% change threshold
        ]

        for _, product in price_changes.iterrows():
            comparison['price_changes'].append({
                'product_id': product['external_id'],
                'name': product['name_current'],
                'old_price': product['regular_price_historical'],
                'new_price': product['regular_price_current'],
                'change_pct': ((product['regular_price_current'] - product['regular_price_historical']) /
                             product['regular_price_historical'] * 100)
            })

        # New products
        current_ids = set(current_df['external_id'])
        historical_ids = set(historical_df['external_id'])
        new_product_ids = current_ids - historical_ids

        for product_id in new_product_ids:
            product = current_df[current_df['external_id'] == product_id].iloc[0]
            comparison['new_products'].append({
                'product_id': product_id,
                'name': product['name'],
                'price': product['regular_price']
            })

        logger.info(f"Historical comparison: {len(comparison['price_changes'])} price changes, "
                   f"{len(comparison['new_products'])} new products")

        return comparison


# Convenience functions
def analyze_product_discounts(df: pd.DataFrame) -> DiscountAnalysis:
    """
    Convenience function to analyze product discounts.

    Args:
        df: DataFrame with product data

    Returns:
        DiscountAnalysis object
    """
    analyzer = DiscountAnalyzer()
    return analyzer.analyze_discounts(df)


def detect_pricing_errors(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convenience function to detect pricing errors.

    Args:
        df: DataFrame with product data

    Returns:
        List of error dictionaries
    """
    analyzer = DiscountAnalyzer()
    analysis = analyzer.analyze_discounts(df)
    return analysis.potential_errors
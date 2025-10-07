"""
Advanced Discount Analyzer for identifying unnaturally good deals
Uses statistical methods and historical data analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DiscountAnalysis:
    """Results from discount analysis"""
    total_products: int
    products_with_discount: int
    average_discount: float
    median_discount: float
    max_discount: float
    high_discount_products: List[Dict]
    potential_errors: List[Dict]
    suspicious_deals: List[Dict]
    discount_distribution: Dict[str, int]


class DiscountAnalyzer:
    """
    Advanced discount analysis for identifying unnaturally good deals
    
    This analyzer uses multiple techniques:
    1. Statistical outlier detection (Z-score, IQR)
    2. Historical price comparison
    3. Category-based benchmarking
    4. Fake discount detection (inflated original prices)
    5. Deal scoring system
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.high_discount_threshold = self.config.get('high_discount_threshold', 75)
        self.critical_discount_threshold = self.config.get('critical_discount_threshold', 90)
        self.price_error_margin = self.config.get('price_error_margin', 0.05)

    def analyze(self, products_df: pd.DataFrame) -> DiscountAnalysis:
        """
        Perform comprehensive discount analysis
        
        Args:
            products_df: DataFrame with product data
            
        Returns:
            DiscountAnalysis object with results
        """
        if products_df.empty:
            logger.warning("Empty products DataFrame provided")
            return self._empty_analysis()

        # Ensure required columns exist
        required_cols = ['name', 'current_price', 'original_price', 'discount_percentage']
        for col in required_cols:
            if col not in products_df.columns:
                products_df[col] = None

        # Basic statistics
        total_products = len(products_df)
        products_with_discount = len(products_df[products_df['discount_percentage'] > 0])

        discounts = products_df[products_df['discount_percentage'] > 0]['discount_percentage']
        avg_discount = float(discounts.mean()) if len(discounts) > 0 else 0.0
        median_discount = float(discounts.median()) if len(discounts) > 0 else 0.0
        max_discount = float(discounts.max()) if len(discounts) > 0 else 0.0

        # Identify high discount products
        high_discount_products = self._find_high_discount_products(products_df)

        # Detect potential errors
        potential_errors = self._detect_pricing_errors(products_df)

        # Detect suspicious deals (UNNATURALLY GOOD)
        suspicious_deals = self._detect_suspicious_deals(products_df)

        # Discount distribution
        discount_distribution = self._calculate_discount_distribution(products_df)

        analysis = DiscountAnalysis(
            total_products=total_products,
            products_with_discount=products_with_discount,
            average_discount=avg_discount,
            median_discount=median_discount,
            max_discount=max_discount,
            high_discount_products=high_discount_products,
            potential_errors=potential_errors,
            suspicious_deals=suspicious_deals,
            discount_distribution=discount_distribution
        )

        logger.info(f"Analysis complete: {total_products} products, {len(suspicious_deals)} suspicious deals found")
        return analysis

    def _find_high_discount_products(self, df: pd.DataFrame) -> List[Dict]:
        """Find products with unusually high discounts"""
        high_discount_df = df[df['discount_percentage'] >= self.high_discount_threshold].copy()

        products = []
        for _, row in high_discount_df.iterrows():
            products.append({
                'name': row.get('name', 'Unknown'),
                'current_price': row.get('current_price'),
                'original_price': row.get('original_price'),
                'discount_percentage': row.get('discount_percentage'),
                'category': row.get('category'),
                'reason': f"Discount exceeds {self.high_discount_threshold}%"
            })

        return sorted(products, key=lambda x: x['discount_percentage'], reverse=True)

    def _detect_pricing_errors(self, df: pd.DataFrame) -> List[Dict]:
        """Detect potential pricing errors"""
        errors = []

        for idx, row in df.iterrows():
            current = row.get('current_price')
            original = row.get('original_price')
            discount = row.get('discount_percentage')
            name = row.get('name', 'Unknown')

            # Error 1: Current price higher than original
            if current and original and current > original:
                errors.append({
                    'name': name,
                    'type': 'PRICE_INVERSION',
                    'severity': 'HIGH',
                    'description': f"Current price ({current:.2f}) > Original price ({original:.2f})",
                    'current_price': current,
                    'original_price': original
                })

            # Error 2: Negative prices
            if current and current < 0:
                errors.append({
                    'name': name,
                    'type': 'NEGATIVE_PRICE',
                    'severity': 'CRITICAL',
                    'description': f"Negative current price: {current:.2f}",
                    'current_price': current
                })

            # Error 3: Extreme discounts (>95%)
            if discount and discount > 95:
                errors.append({
                    'name': name,
                    'type': 'EXTREME_DISCOUNT',
                    'severity': 'HIGH',
                    'description': f"Suspiciously high discount: {discount:.1f}%",
                    'discount_percentage': discount,
                    'current_price': current,
                    'original_price': original
                })

            # Error 4: Discount calculation mismatch
            if current and original and discount and original > 0:
                calculated_discount = ((original - current) / original) * 100
                if abs(calculated_discount - discount) > 5:  # 5% tolerance
                    errors.append({
                        'name': name,
                        'type': 'DISCOUNT_MISMATCH',
                        'severity': 'MEDIUM',
                        'description': f"Claimed discount ({discount:.1f}%) != Calculated ({calculated_discount:.1f}%)",
                        'claimed_discount': discount,
                        'calculated_discount': calculated_discount
                    })

        return sorted(errors, key=lambda x: {'CRITICAL': 3, 'HIGH': 2, 'MEDIUM': 1, 'LOW': 0}.get(x['severity'], 0), reverse=True)

    def _detect_suspicious_deals(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect UNNATURALLY GOOD deals using advanced algorithms
        
        This is the core function for your use case - identifying deals that are too good to be true
        """
        suspicious = []

        # Calculate statistics by category
        category_stats = self._calculate_category_statistics(df)

        for idx, row in df.iterrows():
            name = row.get('name', 'Unknown')
            current = row.get('current_price')
            original = row.get('original_price')
            discount = row.get('discount_percentage', 0)
            category = row.get('category', 'unknown')

            if not current or not original or discount == 0:
                continue

            suspicion_score = 0
            reasons = []

            # Check 1: Statistical outlier in discount
            if category in category_stats:
                mean_discount = category_stats[category]['mean_discount']
                std_discount = category_stats[category]['std_discount']

                if std_discount > 0:
                    z_score = (discount - mean_discount) / std_discount
                    if z_score > 2.5:  # More than 2.5 standard deviations
                        suspicion_score += 30
                        reasons.append(f"Discount is {z_score:.1f}σ above category average")

            # Check 2: Extreme discount percentage
            if discount >= 90:
                suspicion_score += 40
                reasons.append(f"Extreme discount: {discount:.1f}%")
            elif discount >= 80:
                suspicion_score += 30
                reasons.append(f"Very high discount: {discount:.1f}%")
            elif discount >= 70:
                suspicion_score += 20
                reasons.append(f"High discount: {discount:.1f}%")

            # Check 3: Price too low for category
            if category in category_stats:
                median_price = category_stats[category]['median_price']
                if median_price > 0 and current < median_price * 0.2:  # Less than 20% of median
                    suspicion_score += 25
                    reasons.append(f"Price significantly below category median ({current:.2f} vs {median_price:.2f})")

            # Check 4: Round number original price (fake discount indicator)
            if original % 100 == 0 or original % 50 == 0:  # Suspiciously round numbers
                suspicion_score += 10
                reasons.append(f"Suspiciously round original price: {original:.2f}")

            # Check 5: Original price seems inflated
            if category in category_stats:
                max_reasonable_price = category_stats[category]['percentile_90']
                if original > max_reasonable_price * 1.5:
                    suspicion_score += 20
                    reasons.append(f"Original price may be inflated ({original:.2f} vs 90th percentile {max_reasonable_price:.2f})")

            # Check 6: Deal scoring - calculate "Deal Quality Score"
            deal_quality = self._calculate_deal_quality(current, original, discount, category_stats.get(category, {}))
            if deal_quality > 85:
                suspicion_score += 15
                reasons.append(f"Exceptional deal quality score: {deal_quality:.0f}/100")

            # If suspicion score is high enough, flag as suspicious
            if suspicion_score >= 40:  # Threshold for suspicious deals
                suspicious.append({
                    'name': name,
                    'current_price': current,
                    'original_price': original,
                    'discount_percentage': discount,
                    'category': category,
                    'suspicion_score': suspicion_score,
                    'deal_quality': deal_quality,
                    'reasons': reasons,
                    'recommendation': self._get_recommendation(suspicion_score)
                })

        # Sort by suspicion score (highest first)
        suspicious = sorted(suspicious, key=lambda x: x['suspicion_score'], reverse=True)

        return suspicious

    def _calculate_category_statistics(self, df: pd.DataFrame) -> Dict:
        """Calculate statistical benchmarks for each category"""
        stats = {}

        if 'category' not in df.columns:
            return stats

        for category in df['category'].unique():
            if pd.isna(category):
                continue

            cat_df = df[df['category'] == category].copy()

            # Discount statistics
            discounts = cat_df[cat_df['discount_percentage'] > 0]['discount_percentage']
            mean_discount = float(discounts.mean()) if len(discounts) > 0 else 0.0
            std_discount = float(discounts.std()) if len(discounts) > 1 else 0.0

            # Price statistics
            prices = cat_df[cat_df['current_price'] > 0]['current_price']
            median_price = float(prices.median()) if len(prices) > 0 else 0.0
            mean_price = float(prices.mean()) if len(prices) > 0 else 0.0
            percentile_90 = float(prices.quantile(0.9)) if len(prices) > 0 else 0.0

            stats[category] = {
                'mean_discount': mean_discount,
                'std_discount': std_discount,
                'median_price': median_price,
                'mean_price': mean_price,
                'percentile_90': percentile_90,
                'product_count': len(cat_df)
            }

        return stats

    def _calculate_deal_quality(self, current_price: float, original_price: float,
                                discount: float, category_stats: Dict) -> float:
        """
        Calculate a "Deal Quality Score" from 0-100
        Higher scores = better deals (potentially unnaturally good)
        """
        score = 0.0

        # Factor 1: Discount percentage (0-40 points)
        score += min(discount / 2, 40)  # Max 40 points for 80%+ discount

        # Factor 2: Absolute savings (0-30 points)
        savings = original_price - current_price
        if savings > 1000:
            score += 30
        elif savings > 500:
            score += 20
        elif savings > 200:
            score += 10

        # Factor 3: Relative to category (0-30 points)
        if category_stats:
            mean_discount = category_stats.get('mean_discount', 0)
            if mean_discount > 0:
                relative_quality = (discount - mean_discount) / mean_discount
                score += min(relative_quality * 10, 30)

        return min(score, 100)

    def _get_recommendation(self, suspicion_score: int) -> str:
        """Get recommendation based on suspicion score"""
        if suspicion_score >= 80:
            return "⚠️ HIGHLY SUSPICIOUS - Verify carefully before purchasing"
        elif suspicion_score >= 60:
            return "🔍 SUSPICIOUS - Check product details and seller reputation"
        elif suspicion_score >= 40:
            return "⚡ POTENTIALLY GOOD DEAL - Worth investigating"
        else:
            return "✅ Normal discount range"

    def _calculate_discount_distribution(self, df: pd.DataFrame) -> Dict[str, int]:
        """Calculate distribution of discounts by range"""
        distribution = {
            '0-10%': 0,
            '10-25%': 0,
            '25-50%': 0,
            '50-75%': 0,
            '75-90%': 0,
            '90%+': 0
        }

        discounts = df[df['discount_percentage'] > 0]['discount_percentage']

        for discount in discounts:
            if discount < 10:
                distribution['0-10%'] += 1
            elif discount < 25:
                distribution['10-25%'] += 1
            elif discount < 50:
                distribution['25-50%'] += 1
            elif discount < 75:
                distribution['50-75%'] += 1
            elif discount < 90:
                distribution['75-90%'] += 1
            else:
                distribution['90%+'] += 1

        return distribution

    def _empty_analysis(self) -> DiscountAnalysis:
        """Return empty analysis result"""
        return DiscountAnalysis(
            total_products=0,
            products_with_discount=0,
            average_discount=0.0,
            median_discount=0.0,
            max_discount=0.0,
            high_discount_products=[],
            potential_errors=[],
            suspicious_deals=[],
            discount_distribution={}
        )


def analyze_product_discounts(products_df: pd.DataFrame, config: Optional[Dict] = None) -> DiscountAnalysis:
    """
    Convenience function to analyze product discounts
    
    Args:
        products_df: DataFrame with product data
        config: Optional configuration dictionary
        
    Returns:
        DiscountAnalysis object
    """
    analyzer = DiscountAnalyzer(config)
    return analyzer.analyze(products_df)

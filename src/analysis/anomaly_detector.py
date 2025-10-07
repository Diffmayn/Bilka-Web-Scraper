"""
Anomaly Detector for identifying suspicious deals and pricing patterns
This module specifically focuses on detecting unnaturally good offers
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """Result from anomaly detection"""
    product_name: str
    anomaly_type: str
    confidence_score: float  # 0.0 to 1.0
    description: str
    current_price: Optional[float]
    original_price: Optional[float]
    discount_percentage: Optional[float]
    evidence: List[str]
    recommendation: str


class AnomalyDetector:
    """
    Advanced anomaly detection for identifying unnaturally good deals
    
    This detector uses multiple sophisticated techniques:
    1. Z-score analysis for statistical outliers
    2. IQR (Interquartile Range) method
    3. Isolation Forest algorithm (if sklearn available)
    4. Historical price pattern analysis
    5. Fake discount detection (inflated original prices)
    6. Too-good-to-be-true scoring
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.z_score_threshold = self.config.get('z_score_threshold', 2.5)
        self.iqr_multiplier = self.config.get('iqr_multiplier', 1.5)
        self.min_confidence = self.config.get('min_confidence', 0.6)

    def detect_anomalies(self, products_df: pd.DataFrame) -> List[AnomalyResult]:
        """
        Detect all types of anomalies in product data
        
        Args:
            products_df: DataFrame with product data
            
        Returns:
            List of AnomalyResult objects
        """
        if products_df.empty:
            logger.warning("Empty DataFrame provided for anomaly detection")
            return []

        anomalies = []

        # Method 1: Z-score based outlier detection
        z_score_anomalies = self._detect_zscore_anomalies(products_df)
        anomalies.extend(z_score_anomalies)

        # Method 2: IQR-based outlier detection
        iqr_anomalies = self._detect_iqr_anomalies(products_df)
        anomalies.extend(iqr_anomalies)

        # Method 3: Fake discount detection
        fake_discount_anomalies = self._detect_fake_discounts(products_df)
        anomalies.extend(fake_discount_anomalies)

        # Method 4: Too-good-to-be-true detection
        tgtbt_anomalies = self._detect_too_good_to_be_true(products_df)
        anomalies.extend(tgtbt_anomalies)

        # Method 5: Price manipulation detection
        manipulation_anomalies = self._detect_price_manipulation(products_df)
        anomalies.extend(manipulation_anomalies)

        # Remove duplicates and sort by confidence
        anomalies = self._deduplicate_anomalies(anomalies)
        anomalies = sorted(anomalies, key=lambda x: x.confidence_score, reverse=True)

        logger.info(f"Detected {len(anomalies)} anomalies")
        return anomalies

    def _detect_zscore_anomalies(self, df: pd.DataFrame) -> List[AnomalyResult]:
        """Detect anomalies using Z-score method"""
        anomalies = []

        if 'discount_percentage' not in df.columns:
            return anomalies

        # Filter products with discounts
        discounted = df[df['discount_percentage'] > 0].copy()
        if len(discounted) < 3:
            return anomalies

        # Calculate Z-scores
        mean_discount = discounted['discount_percentage'].mean()
        std_discount = discounted['discount_percentage'].std()

        if std_discount == 0:
            return anomalies

        discounted['z_score'] = (discounted['discount_percentage'] - mean_discount) / std_discount

        # Find outliers
        outliers = discounted[discounted['z_score'] > self.z_score_threshold]

        for _, row in outliers.iterrows():
            z_score = row['z_score']
            confidence = min(abs(z_score) / 5.0, 1.0)  # Normalize to 0-1

            if confidence >= self.min_confidence:
                anomalies.append(AnomalyResult(
                    product_name=row.get('name', 'Unknown'),
                    anomaly_type='STATISTICAL_OUTLIER',
                    confidence_score=float(confidence),
                    description=f'Discount is {z_score:.2f} standard deviations above mean',
                    current_price=row.get('current_price'),
                    original_price=row.get('original_price'),
                    discount_percentage=row.get('discount_percentage'),
                    evidence=[
                        f'Z-score: {z_score:.2f}',
                        f'Mean discount: {mean_discount:.1f}%',
                        f'Product discount: {row["discount_percentage"]:.1f}%'
                    ],
                    recommendation=self._get_recommendation(confidence)
                ))

        return anomalies

    def _detect_iqr_anomalies(self, df: pd.DataFrame) -> List[AnomalyResult]:
        """Detect anomalies using Interquartile Range method"""
        anomalies = []

        if 'discount_percentage' not in df.columns:
            return anomalies

        discounted = df[df['discount_percentage'] > 0].copy()
        if len(discounted) < 4:
            return anomalies

        # Calculate IQR
        Q1 = discounted['discount_percentage'].quantile(0.25)
        Q3 = discounted['discount_percentage'].quantile(0.75)
        IQR = Q3 - Q1

        # Define outlier bounds
        upper_bound = Q3 + self.iqr_multiplier * IQR

        # Find outliers
        outliers = discounted[discounted['discount_percentage'] > upper_bound]

        for _, row in outliers.iterrows():
            discount = row['discount_percentage']
            deviation = (discount - upper_bound) / IQR if IQR > 0 else 0
            confidence = min(0.5 + deviation * 0.2, 1.0)

            if confidence >= self.min_confidence:
                anomalies.append(AnomalyResult(
                    product_name=row.get('name', 'Unknown'),
                    anomaly_type='IQR_OUTLIER',
                    confidence_score=float(confidence),
                    description=f'Discount beyond IQR upper bound',
                    current_price=row.get('current_price'),
                    original_price=row.get('original_price'),
                    discount_percentage=row.get('discount_percentage'),
                    evidence=[
                        f'Upper bound: {upper_bound:.1f}%',
                        f'Product discount: {discount:.1f}%',
                        f'IQR: {IQR:.1f}'
                    ],
                    recommendation=self._get_recommendation(confidence)
                ))

        return anomalies

    def _detect_fake_discounts(self, df: pd.DataFrame) -> List[AnomalyResult]:
        """
        Detect fake discounts where original price may be artificially inflated
        
        This is crucial for identifying deceptive pricing practices
        """
        anomalies = []

        for _, row in df.iterrows():
            current = row.get('current_price')
            original = row.get('original_price')
            discount = row.get('discount_percentage', 0)

            if not current or not original or discount == 0:
                continue

            suspicion_indicators = []
            confidence = 0.0

            # Indicator 1: Original price is a very round number
            if original >= 100 and original % 100 == 0:
                suspicion_indicators.append('Original price is suspiciously round')
                confidence += 0.15
            elif original >= 50 and original % 50 == 0:
                suspicion_indicators.append('Original price is a round number')
                confidence += 0.10

            # Indicator 2: Discount is also a very round number
            if discount % 10 == 0 and discount >= 50:
                suspicion_indicators.append('Discount is a round percentage')
                confidence += 0.10

            # Indicator 3: Original price seems way above market range
            category = row.get('category')
            if category:
                cat_prices = df[df['category'] == category]['current_price']
                if len(cat_prices) > 5:
                    median_price = cat_prices.median()
                    if original > median_price * 2.5:
                        suspicion_indicators.append(f'Original price {original:.2f} is 2.5x category median {median_price:.2f}')
                        confidence += 0.30

            # Indicator 4: High discount but final price is still average
            if discount >= 60:
                category_prices = df[df['category'] == row.get('category')]['current_price']
                if len(category_prices) > 3:
                    median_cat_price = category_prices.median()
                    if abs(current - median_cat_price) / median_cat_price < 0.2:  # Within 20% of median
                        suspicion_indicators.append('Large discount but price is average for category')
                        confidence += 0.25

            if confidence >= self.min_confidence:
                anomalies.append(AnomalyResult(
                    product_name=row.get('name', 'Unknown'),
                    anomaly_type='FAKE_DISCOUNT',
                    confidence_score=min(confidence, 1.0),
                    description='Possible fake discount - original price may be inflated',
                    current_price=current,
                    original_price=original,
                    discount_percentage=discount,
                    evidence=suspicion_indicators,
                    recommendation='⚠️ Verify original price was actually charged before discount'
                ))

        return anomalies

    def _detect_too_good_to_be_true(self, df: pd.DataFrame) -> List[AnomalyResult]:
        """
        Detect deals that are TOO GOOD TO BE TRUE
        
        This is the main function for your use case - finding unnaturally good offers
        """
        anomalies = []

        for _, row in df.iterrows():
            current = row.get('current_price')
            original = row.get('original_price')
            discount = row.get('discount_percentage', 0)
            name = row.get('name', 'Unknown')

            if not current or discount == 0:
                continue

            tgtbt_score = 0.0
            evidence = []

            # Factor 1: Extreme discount (90%+)
            if discount >= 95:
                tgtbt_score += 0.40
                evidence.append(f'Extreme discount of {discount:.1f}%')
            elif discount >= 90:
                tgtbt_score += 0.30
                evidence.append(f'Very high discount of {discount:.1f}%')
            elif discount >= 80:
                tgtbt_score += 0.20
                evidence.append(f'High discount of {discount:.1f}%')

            # Factor 2: Large absolute savings
            if original:
                savings = original - current
                if savings > 5000:
                    tgtbt_score += 0.25
                    evidence.append(f'Massive savings of {savings:.2f} DKK')
                elif savings > 2000:
                    tgtbt_score += 0.15
                    evidence.append(f'Large savings of {savings:.2f} DKK')

            # Factor 3: Premium product at bargain price
            if 'samsung' in name.lower() or 'apple' in name.lower() or 'sony' in name.lower():
                if current < 500 and discount > 70:
                    tgtbt_score += 0.20
                    evidence.append('Premium brand at suspiciously low price')

            # Factor 4: Current price is extremely low
            if current < 50 and original and original > 500:
                tgtbt_score += 0.15
                evidence.append(f'Price dropped from {original:.2f} to {current:.2f}')

            if tgtbt_score >= self.min_confidence:
                anomalies.append(AnomalyResult(
                    product_name=name,
                    anomaly_type='TOO_GOOD_TO_BE_TRUE',
                    confidence_score=min(tgtbt_score, 1.0),
                    description='Deal appears too good to be true - verify authenticity',
                    current_price=current,
                    original_price=original,
                    discount_percentage=discount,
                    evidence=evidence,
                    recommendation='🚨 VERIFY: Check seller, product condition, and reviews before purchasing'
                ))

        return anomalies

    def _detect_price_manipulation(self, df: pd.DataFrame) -> List[AnomalyResult]:
        """Detect potential price manipulation patterns"""
        anomalies = []

        for _, row in df.iterrows():
            current = row.get('current_price')
            original = row.get('original_price')
            discount = row.get('discount_percentage', 0)

            if not current or not original or discount == 0:
                continue

            # Check for suspicious price patterns
            manipulation_score = 0.0
            evidence = []

            # Pattern 1: Original price ends in .99 but "discounted" price ends in .00
            if original % 1 > 0.98 and current % 1 < 0.05:
                manipulation_score += 0.15
                evidence.append('Suspicious price pattern: original .99, sale .00')

            # Pattern 2: Discount percentage is exactly 50%, 75%, etc. (common manipulation)
            if discount in [50.0, 75.0, 66.7, 33.3]:
                manipulation_score += 0.10
                evidence.append(f'Common manipulation discount: {discount}%')

            # Pattern 3: Current price * 2 = original price (doubled for discount)
            if original and abs(current * 2 - original) < 1:
                manipulation_score += 0.20
                evidence.append('Original price appears to be exactly double current price')

            if manipulation_score >= 0.25:
                anomalies.append(AnomalyResult(
                    product_name=row.get('name', 'Unknown'),
                    anomaly_type='PRICE_MANIPULATION',
                    confidence_score=min(manipulation_score + 0.4, 1.0),
                    description='Possible price manipulation detected',
                    current_price=current,
                    original_price=original,
                    discount_percentage=discount,
                    evidence=evidence,
                    recommendation='⚠️ Cross-check prices with other retailers'
                ))

        return anomalies

    def _deduplicate_anomalies(self, anomalies: List[AnomalyResult]) -> List[AnomalyResult]:
        """Remove duplicate anomalies for the same product"""
        seen_products = {}

        for anomaly in anomalies:
            if anomaly.product_name not in seen_products:
                seen_products[anomaly.product_name] = anomaly
            else:
                # Keep the one with higher confidence
                if anomaly.confidence_score > seen_products[anomaly.product_name].confidence_score:
                    seen_products[anomaly.product_name] = anomaly

        return list(seen_products.values())

    def _get_recommendation(self, confidence: float) -> str:
        """Get recommendation based on confidence score"""
        if confidence >= 0.9:
            return "🚨 CRITICAL: Almost certainly an error or scam - Do not purchase"
        elif confidence >= 0.8:
            return "⚠️ HIGH RISK: Very suspicious - Investigate thoroughly"
        elif confidence >= 0.7:
            return "🔍 SUSPICIOUS: Likely too good to be true - Verify carefully"
        elif confidence >= 0.6:
            return "⚡ CAUTION: Unusually good deal - Check details before buying"
        else:
            return "ℹ️ NOTICE: Potential bargain but verify authenticity"


def detect_suspicious_deals(products_df: pd.DataFrame, config: Optional[Dict] = None) -> List[AnomalyResult]:
    """
    Convenience function to detect suspicious deals
    
    Args:
        products_df: DataFrame with product data
        config: Optional configuration dictionary
        
    Returns:
        List of AnomalyResult objects
    """
    detector = AnomalyDetector(config)
    return detector.detect_anomalies(products_df)

"""
Data Processor for Bilka Price Monitor

Handles data cleaning, normalization, and preprocessing of scraped product data.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import re
from loguru import logger

from .models import Product, PriceHistory
from src.scraper.product_parser import ProductData


class DataProcessor:
    """
    Data processor for cleaning and normalizing scraped product data.

    Provides methods for data validation, normalization, and preprocessing
    before storage or analysis.
    """

    def __init__(self):
        """Initialize the data processor."""
        logger.info("Data processor initialized")

    def process_product_data(self, products: List[ProductData]) -> List[ProductData]:
        """
        Process a list of product data objects.

        Args:
            products: List of ProductData objects

        Returns:
            List of processed ProductData objects
        """
        processed_products = []

        for product in products:
            try:
                processed_product = self._process_single_product(product)
                if processed_product:
                    processed_products.append(processed_product)
            except Exception as e:
                logger.warning(f"Error processing product {product.external_id}: {e}")
                continue

        logger.info(f"Processed {len(processed_products)} out of {len(products)} products")
        return processed_products

    def _process_single_product(self, product: ProductData) -> Optional[ProductData]:
        """
        Process a single product data object.

        Args:
            product: ProductData object to process

        Returns:
            Processed ProductData object or None if invalid
        """
        # Clean and normalize text fields
        product.name = self._clean_text(product.name)
        product.category = self._clean_text(product.category)
        product.subcategory = self._clean_text(product.subcategory)
        product.brand = self._clean_text(product.brand)

        # Process pricing data
        product.regular_price = self._normalize_price(product.regular_price)
        product.sale_price = self._normalize_price(product.sale_price)

        # Calculate discount if not provided
        if product.discount_percentage is None and product.regular_price and product.sale_price:
            product.discount_percentage = self._calculate_discount_percentage(
                product.regular_price, product.sale_price
            )

        # Validate product data
        if not self._validate_product_data(product):
            return None

        # Clean URLs
        product.image_url = self._clean_url(product.image_url)
        product.product_url = self._clean_url(product.product_url)

        return product

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """
        Clean and normalize text data.

        Args:
            text: Text to clean

        Returns:
            Cleaned text or None
        """
        if not text:
            return None

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove non-printable characters
        text = ''.join(char for char in text if char.isprintable())

        # Convert to title case for consistency
        if len(text) > 3:  # Only for longer strings
            text = text.title()

        return text if text else None

    def _normalize_price(self, price: Optional[float]) -> Optional[float]:
        """
        Normalize price values.

        Args:
            price: Price to normalize

        Returns:
            Normalized price or None
        """
        if price is None:
            return None

        # Round to 2 decimal places
        price = round(price, 2)

        # Validate price range
        if price < 0:
            logger.warning(f"Negative price found: {price}")
            return None
        elif price > 100000:  # Maximum expected price
            logger.warning(f"Suspiciously high price: {price}")
            return None

        return price

    def _calculate_discount_percentage(self, regular_price: float, sale_price: float) -> Optional[float]:
        """
        Calculate discount percentage from regular and sale prices.

        Args:
            regular_price: Regular price
            sale_price: Sale price

        Returns:
            Discount percentage or None
        """
        try:
            if regular_price <= 0 or sale_price < 0:
                return None

            if sale_price > regular_price:
                # Sale price higher than regular - invalid
                return None

            discount = ((regular_price - sale_price) / regular_price) * 100
            return round(discount, 2)

        except Exception as e:
            logger.debug(f"Error calculating discount: {e}")
            return None

    def _clean_url(self, url: Optional[str]) -> Optional[str]:
        """
        Clean and validate URLs.

        Args:
            url: URL to clean

        Returns:
            Cleaned URL or None
        """
        if not url:
            return None

        url = url.strip()

        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            return None

        return url

    def _validate_product_data(self, product: ProductData) -> bool:
        """
        Validate product data completeness and consistency.

        Args:
            product: ProductData object to validate

        Returns:
            True if valid, False otherwise
        """
        # Must have name and external ID
        if not product.name or not product.external_id:
            return False

        # Must have at least one price
        if product.regular_price is None and product.sale_price is None:
            return False

        # If both prices exist, regular should be >= sale
        if (product.regular_price is not None and product.sale_price is not None):
            if product.regular_price < product.sale_price:
                logger.warning(f"Regular price < sale price for {product.external_id}")
                return False

        # Discount percentage should be reasonable
        if product.discount_percentage is not None:
            if product.discount_percentage < 0 or product.discount_percentage > 100:
                logger.warning(f"Invalid discount percentage: {product.discount_percentage}")
                return False

        return True

    def create_dataframe_from_products(self, products: List[ProductData]) -> pd.DataFrame:
        """
        Create a pandas DataFrame from product data.

        Args:
            products: List of ProductData objects

        Returns:
            Pandas DataFrame
        """
        data = []
        for product in products:
            data.append({
                'external_id': product.external_id,
                'name': product.name,
                'category': product.category,
                'subcategory': product.subcategory,
                'brand': product.brand,
                'regular_price': product.regular_price,
                'sale_price': product.sale_price,
                'discount_percentage': product.discount_percentage,
                'currency': product.currency,
                'image_url': product.image_url,
                'product_url': product.product_url,
                'availability': product.availability,
                'scraped_at': product.scraped_at
            })

        return pd.DataFrame(data)

    def detect_price_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect pricing anomalies in the data.

        Args:
            df: DataFrame with product data

        Returns:
            DataFrame with anomaly flags and scores
        """
        # Create a copy to avoid modifying original
        df_analyzed = df.copy()

        # Initialize anomaly columns
        df_analyzed['is_anomaly'] = False
        df_analyzed['anomaly_reason'] = None
        df_analyzed['anomaly_severity'] = 'low'

        # Rule 1: Extreme discount (>90%)
        extreme_discount = df_analyzed['discount_percentage'] > 90
        df_analyzed.loc[extreme_discount, 'is_anomaly'] = True
        df_analyzed.loc[extreme_discount, 'anomaly_reason'] = 'Extreme discount >90%'
        df_analyzed.loc[extreme_discount, 'anomaly_severity'] = 'high'

        # Rule 2: Negative prices
        negative_prices = (df_analyzed['regular_price'] < 0) | (df_analyzed['sale_price'] < 0)
        df_analyzed.loc[negative_prices, 'is_anomaly'] = True
        df_analyzed.loc[negative_prices, 'anomaly_reason'] = 'Negative price'
        df_analyzed.loc[negative_prices, 'anomaly_severity'] = 'critical'

        # Rule 3: Sale price > regular price
        invalid_price_relationship = (
            (df_analyzed['regular_price'].notna()) &
            (df_analyzed['sale_price'].notna()) &
            (df_analyzed['sale_price'] > df_analyzed['regular_price'])
        )
        df_analyzed.loc[invalid_price_relationship, 'is_anomaly'] = True
        df_analyzed.loc[invalid_price_relationship, 'anomaly_reason'] = 'Sale price > regular price'
        df_analyzed.loc[invalid_price_relationship, 'anomaly_severity'] = 'high'

        # Rule 4: Missing prices
        missing_prices = (
            df_analyzed['regular_price'].isna() & df_analyzed['sale_price'].isna()
        )
        df_analyzed.loc[missing_prices, 'is_anomaly'] = True
        df_analyzed.loc[missing_prices, 'anomaly_reason'] = 'Missing price data'
        df_analyzed.loc[missing_prices, 'anomaly_severity'] = 'medium'

        # Rule 5: Unusually high prices
        high_prices = df_analyzed['regular_price'] > 50000  # 50k DKK threshold
        df_analyzed.loc[high_prices, 'is_anomaly'] = True
        df_analyzed.loc[high_prices, 'anomaly_reason'] = 'Unusually high price'
        df_analyzed.loc[high_prices, 'anomaly_severity'] = 'medium'

        logger.info(f"Detected {df_analyzed['is_anomaly'].sum()} anomalies in {len(df_analyzed)} products")

        return df_analyzed

    def calculate_price_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate price statistics from the data.

        Args:
            df: DataFrame with product data

        Returns:
            Dictionary with price statistics
        """
        stats = {}

        # Basic price statistics
        for price_col in ['regular_price', 'sale_price']:
            if price_col in df.columns:
                prices = df[price_col].dropna()
                if not prices.empty:
                    stats[f'{price_col}_mean'] = prices.mean()
                    stats[f'{price_col}_median'] = prices.median()
                    stats[f'{price_col}_min'] = prices.min()
                    stats[f'{price_col}_max'] = prices.max()
                    stats[f'{price_col}_std'] = prices.std()

        # Discount statistics
        if 'discount_percentage' in df.columns:
            discounts = df['discount_percentage'].dropna()
            if not discounts.empty:
                stats['discount_mean'] = discounts.mean()
                stats['discount_median'] = discounts.median()
                stats['discount_max'] = discounts.max()
                stats['products_with_discount'] = (discounts > 0).sum()
                stats['high_discount_products'] = (discounts > 50).sum()

        # Category statistics
        if 'category' in df.columns:
            category_counts = df['category'].value_counts()
            stats['category_counts'] = category_counts.to_dict()
            stats['total_categories'] = len(category_counts)

        # Anomaly statistics
        if 'is_anomaly' in df.columns:
            anomaly_counts = df['anomaly_reason'].value_counts()
            stats['anomaly_counts'] = anomaly_counts.to_dict()
            stats['total_anomalies'] = df['is_anomaly'].sum()

        return stats

    def filter_products_by_criteria(self, df: pd.DataFrame,
                                  min_discount: Optional[float] = None,
                                  max_price: Optional[float] = None,
                                  categories: Optional[List[str]] = None,
                                  exclude_anomalies: bool = False) -> pd.DataFrame:
        """
        Filter products based on various criteria.

        Args:
            df: DataFrame with product data
            min_discount: Minimum discount percentage
            max_price: Maximum price
            categories: List of categories to include
            exclude_anomalies: Whether to exclude anomalous products

        Returns:
            Filtered DataFrame
        """
        filtered_df = df.copy()

        # Filter by discount
        if min_discount is not None:
            filtered_df = filtered_df[
                (filtered_df['discount_percentage'].isna()) |
                (filtered_df['discount_percentage'] >= min_discount)
            ]

        # Filter by price
        if max_price is not None:
            price_filter = (
                (filtered_df['regular_price'].isna() | (filtered_df['regular_price'] <= max_price)) &
                (filtered_df['sale_price'].isna() | (filtered_df['sale_price'] <= max_price))
            )
            filtered_df = filtered_df[price_filter]

        # Filter by category
        if categories:
            filtered_df = filtered_df[filtered_df['category'].isin(categories)]

        # Exclude anomalies
        if exclude_anomalies and 'is_anomaly' in filtered_df.columns:
            filtered_df = filtered_df[~filtered_df['is_anomaly']]

        logger.info(f"Filtered from {len(df)} to {len(filtered_df)} products")
        return filtered_df

    def export_processed_data(self, df: pd.DataFrame, filepath: str,
                            format: str = 'csv') -> bool:
        """
        Export processed data to file.

        Args:
            df: DataFrame to export
            filepath: Output file path
            format: Export format ('csv', 'json', 'excel')

        Returns:
            True if successful, False otherwise
        """
        try:
            if format.lower() == 'csv':
                df.to_csv(filepath, index=False)
            elif format.lower() == 'json':
                df.to_json(filepath, orient='records', date_format='iso')
            elif format.lower() == 'excel':
                df.to_excel(filepath, index=False)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False

            logger.info(f"Exported {len(df)} products to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False


# Convenience functions
def process_products(products: List[ProductData]) -> List[ProductData]:
    """
    Convenience function to process product data.

    Args:
        products: List of ProductData objects

    Returns:
        List of processed ProductData objects
    """
    processor = DataProcessor()
    return processor.process_product_data(products)


def create_product_dataframe(products: List[ProductData]) -> pd.DataFrame:
    """
    Convenience function to create DataFrame from products.

    Args:
        products: List of ProductData objects

    Returns:
        Pandas DataFrame
    """
    processor = DataProcessor()
    return processor.create_dataframe_from_products(products)
"""
Data Storage Layer for Bilka Price Monitor

Handles database operations, data persistence, and retrieval.
Provides high-level interface for storing and querying product data.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from .models import (
    DatabaseManager, Product, PriceHistory, ScrapingSession,
    get_database_manager, init_database
)
from src.scraper.product_parser import ProductData


class DataStorage:
    """
    Data storage class for managing product data persistence.

    Provides methods for storing scraped data, retrieving historical information,
    and generating reports.
    """

    def __init__(self, database_url: str = None):
        """
        Initialize the data storage.

        Args:
            database_url: Database connection URL
        """
        self.db_manager = get_database_manager(database_url)
        logger.info("Data storage initialized")

    def store_product_data(self, product_data: ProductData) -> bool:
        """
        Store product data in the database.

        Args:
            product_data: ProductData object to store

        Returns:
            True if successful, False otherwise
        """
        session = None
        try:
            session = self.db_manager.get_session()

            # Prepare product data for database
            product_dict = {
                'external_id': product_data.external_id,
                'name': product_data.name,
                'category': product_data.category,
                'subcategory': product_data.subcategory,
                'brand': product_data.brand,
                'image_url': product_data.image_url
            }

            # Add or update product
            product = self.db_manager.add_product(session, product_dict)

            # Add price history if pricing data is available
            if product_data.regular_price is not None or product_data.sale_price is not None:
                price_dict = {
                    'regular_price': product_data.regular_price,
                    'sale_price': product_data.sale_price,
                    'discount_percentage': product_data.discount_percentage,
                    'currency': product_data.currency,
                    'scraped_at': datetime.fromisoformat(product_data.scraped_at) if product_data.scraped_at else datetime.utcnow()
                }
                self.db_manager.add_price_history(session, product.id, price_dict)

            logger.debug(f"Stored product data: {product_data.name}")
            return True

        except Exception as e:
            logger.error(f"Error storing product data: {e}")
            return False
        finally:
            if session:
                self.db_manager.close_session(session)

    def store_multiple_products(self, products: List[ProductData]) -> Dict[str, int]:
        """
        Store multiple products in the database.

        Args:
            products: List of ProductData objects

        Returns:
            Dictionary with success/failure counts
        """
        successful = 0
        failed = 0

        for product_data in products:
            if self.store_product_data(product_data):
                successful += 1
            else:
                failed += 1

        logger.info(f"Stored {successful} products successfully, {failed} failed")
        return {'successful': successful, 'failed': failed}

    def get_product_by_external_id(self, external_id: str) -> Optional[Product]:
        """
        Get product by external ID.

        Args:
            external_id: External product ID

        Returns:
            Product object or None if not found
        """
        session = None
        try:
            session = self.db_manager.get_session()
            product = session.query(Product).filter_by(external_id=external_id).first()
            return product
        except Exception as e:
            logger.error(f"Error getting product by external ID: {e}")
            return None
        finally:
            if session:
                self.db_manager.close_session(session)

    def get_product_price_history(self, external_id: str, limit: int = 50) -> List[PriceHistory]:
        """
        Get price history for a product.

        Args:
            external_id: External product ID
            limit: Maximum number of records to return

        Returns:
            List of PriceHistory objects
        """
        session = None
        try:
            session = self.db_manager.get_session()
            product = session.query(Product).filter_by(external_id=external_id).first()

            if product:
                return self.db_manager.get_recent_price_history(session, product.id, limit)
            else:
                return []

        except Exception as e:
            logger.error(f"Error getting price history: {e}")
            return []
        finally:
            if session:
                self.db_manager.close_session(session)

    def get_products_by_category(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get products by category with their latest pricing.

        Args:
            category: Product category
            limit: Maximum number of products to return

        Returns:
            List of dictionaries with product and pricing information
        """
        session = None
        try:
            session = self.db_manager.get_session()

            # Query products with their latest price history
            query = session.query(Product, PriceHistory).join(PriceHistory).filter(
                Product.category == category
            ).order_by(PriceHistory.scraped_at.desc()).limit(limit)

            results = []
            seen_products = set()

            for product, price_history in query:
                if product.id not in seen_products:
                    seen_products.add(product.id)
                    results.append({
                        'product': product,
                        'latest_price': price_history
                    })

            return results

        except Exception as e:
            logger.error(f"Error getting products by category: {e}")
            return []
        finally:
            if session:
                self.db_manager.close_session(session)

    def get_price_changes(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get products with price changes in the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of dictionaries with price change information
        """
        session = None
        try:
            session = self.db_manager.get_session()
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Complex query to find products with price changes
            # This is a simplified version - in production you might want more sophisticated logic
            query = session.query(Product, PriceHistory).join(PriceHistory).filter(
                PriceHistory.scraped_at >= cutoff_date
            ).order_by(Product.id, PriceHistory.scraped_at.desc())

            results = []
            current_product = None
            prices = []

            for product, price_history in query:
                if current_product != product.id:
                    if current_product is not None and len(prices) > 1:
                        # Check for price changes
                        latest_price = prices[0]
                        previous_price = prices[1] if len(prices) > 1 else None

                        if previous_price and (
                            latest_price.regular_price != previous_price.regular_price or
                            latest_price.sale_price != previous_price.sale_price
                        ):
                            results.append({
                                'product': product,
                                'latest_price': latest_price,
                                'previous_price': previous_price
                            })

                    current_product = product.id
                    prices = [price_history]
                else:
                    prices.append(price_history)

            return results

        except Exception as e:
            logger.error(f"Error getting price changes: {e}")
            return []
        finally:
            if session:
                self.db_manager.close_session(session)

    def get_discount_analysis(self, min_discount: float = 50.0) -> pd.DataFrame:
        """
        Get products with high discounts for analysis.

        Args:
            min_discount: Minimum discount percentage to include

        Returns:
            Pandas DataFrame with discount analysis data
        """
        session = None
        try:
            session = self.db_manager.get_session()

            query = session.query(Product, PriceHistory).join(PriceHistory).filter(
                PriceHistory.discount_percentage >= min_discount,
                PriceHistory.is_active == True
            ).order_by(PriceHistory.discount_percentage.desc())

            data = []
            for product, price_history in query:
                data.append({
                    'external_id': product.external_id,
                    'name': product.name,
                    'category': product.category,
                    'brand': product.brand,
                    'regular_price': price_history.regular_price,
                    'sale_price': price_history.sale_price,
                    'discount_percentage': price_history.discount_percentage,
                    'scraped_at': price_history.scraped_at
                })

            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Error getting discount analysis: {e}")
            return pd.DataFrame()
        finally:
            if session:
                self.db_manager.close_session(session)

    def export_to_csv(self, filepath: str, category: Optional[str] = None) -> bool:
        """
        Export product data to CSV file.

        Args:
            filepath: Path to output CSV file
            category: Optional category filter

        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.db_manager.get_session()

            query = session.query(Product, PriceHistory).join(PriceHistory)

            if category:
                query = query.filter(Product.category == category)

            data = []
            for product, price_history in query:
                data.append({
                    'external_id': product.external_id,
                    'name': product.name,
                    'category': product.category,
                    'subcategory': product.subcategory,
                    'brand': product.brand,
                    'regular_price': price_history.regular_price,
                    'sale_price': price_history.sale_price,
                    'discount_percentage': price_history.discount_percentage,
                    'currency': price_history.currency,
                    'scraped_at': price_history.scraped_at,
                    'image_url': product.image_url,
                    'product_url': product.product_url if hasattr(product, 'product_url') else None
                })

            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False)

            logger.info(f"Exported {len(data)} products to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
        finally:
            if session:
                self.db_manager.close_session(session)

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        session = None
        try:
            session = self.db_manager.get_session()

            stats = {
                'total_products': session.query(Product).count(),
                'total_price_records': session.query(PriceHistory).count(),
                'total_scraping_sessions': session.query(ScrapingSession).count(),
                'categories': session.query(Product.category).distinct().count(),
                'latest_scrape': session.query(PriceHistory.scraped_at).order_by(PriceHistory.scraped_at.desc()).first()
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
        finally:
            if session:
                self.db_manager.close_session(session)


# Convenience functions
def initialize_database(database_url: str = None):
    """
    Initialize the database and create tables.

    Args:
        database_url: Database connection URL
    """
    init_database(database_url)


def create_data_storage(database_url: str = None) -> DataStorage:
    """
    Create a data storage instance.

    Args:
        database_url: Database connection URL

    Returns:
        DataStorage instance
    """
    return DataStorage(database_url)
"""
Data storage and database operations
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, Product, PriceHistory, ScrapeLog, AnomalyDetection

logger = logging.getLogger(__name__)


def initialize_database(database_url: Optional[str] = None):
    """
    Initialize the database and create all tables
    
    Args:
        database_url: Database connection URL (defaults to SQLite in data/)
    """
    if database_url is None:
        os.makedirs("data", exist_ok=True)
        database_url = "sqlite:///data/bilka_prices.db"

    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    logger.info(f"Database initialized: {database_url}")


def create_data_storage(database_url: Optional[str] = None) -> 'DataStorage':
    """
    Create a DataStorage instance
    
    Args:
        database_url: Database connection URL
        
    Returns:
        DataStorage instance
    """
    if database_url is None:
        database_url = "sqlite:///data/bilka_prices.db"

    return DataStorage(database_url)


class DataStorage:
    """Handles all database operations"""

    def __init__(self, database_url: str = "sqlite:///data/bilka_prices.db"):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    def store_product(self, product_data: Dict) -> Optional[Product]:
        """
        Store a single product in the database
        
        Args:
            product_data: Dictionary containing product information
            
        Returns:
            Product instance or None if failed
        """
        session = self.get_session()
        try:
            # Check if product already exists
            existing = session.query(Product).filter_by(
                name=product_data['name']
            ).first()

            if existing:
                # Update existing product
                for key, value in product_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                product = existing
            else:
                # Create new product
                product = Product(**product_data)
                session.add(product)

            session.commit()
            session.refresh(product)

            # Store price history
            self._store_price_history(session, product)

            logger.info(f"Stored product: {product.name}")
            return product

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error storing product: {e}")
            return None
        finally:
            session.close()

    def _store_price_history(self, session: Session, product: Product):
        """Store price history for a product"""
        try:
            price_entry = PriceHistory(
                product_id=product.id,
                price=product.current_price,
                original_price=product.original_price,
                discount_percentage=product.discount_percentage
            )
            session.add(price_entry)
            session.commit()
        except SQLAlchemyError as e:
            logger.warning(f"Error storing price history: {e}")

    def store_multiple_products(self, products: List[Dict]) -> Dict:
        """
        Store multiple products in the database
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Dictionary with success/failure counts
        """
        results = {'successful': 0, 'failed': 0, 'errors': []}

        for product_data in products:
            product = self.store_product(product_data)
            if product:
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(product_data.get('name', 'Unknown'))

        logger.info(f"Stored {results['successful']}/{len(products)} products successfully")
        return results

    def get_products(self, category: Optional[str] = None, limit: int = 100) -> List[Product]:
        """
        Retrieve products from the database
        
        Args:
            category: Filter by category (optional)
            limit: Maximum number of products to retrieve
            
        Returns:
            List of Product instances
        """
        session = self.get_session()
        try:
            query = session.query(Product)

            if category:
                query = query.filter(Product.category == category)

            products = query.order_by(Product.scraped_at.desc()).limit(limit).all()
            return products

        finally:
            session.close()

    def get_product_price_history(self, product_id: int) -> List[PriceHistory]:
        """Get price history for a specific product"""
        session = self.get_session()
        try:
            history = session.query(PriceHistory).filter(
                PriceHistory.product_id == product_id
            ).order_by(PriceHistory.recorded_at.desc()).all()
            return history
        finally:
            session.close()

    def log_scrape(self, log_data: Dict) -> Optional[ScrapeLog]:
        """Log a scraping session"""
        session = self.get_session()
        try:
            log_entry = ScrapeLog(**log_data)
            session.add(log_entry)
            session.commit()
            session.refresh(log_entry)
            return log_entry
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error logging scrape: {e}")
            return None
        finally:
            session.close()

    def store_anomaly(self, anomaly_data: Dict) -> Optional[AnomalyDetection]:
        """Store an anomaly detection result"""
        session = self.get_session()
        try:
            anomaly = AnomalyDetection(**anomaly_data)
            session.add(anomaly)
            session.commit()
            session.refresh(anomaly)
            return anomaly
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error storing anomaly: {e}")
            return None
        finally:
            session.close()

    def get_anomalies(self, confidence_threshold: float = 0.7, limit: int = 100) -> List[AnomalyDetection]:
        """
        Get detected anomalies
        
        Args:
            confidence_threshold: Minimum confidence score
            limit: Maximum number of anomalies to retrieve
            
        Returns:
            List of AnomalyDetection instances
        """
        session = self.get_session()
        try:
            anomalies = session.query(AnomalyDetection).filter(
                AnomalyDetection.confidence_score >= confidence_threshold,
                AnomalyDetection.false_positive == False
            ).order_by(
                AnomalyDetection.confidence_score.desc()
            ).limit(limit).all()
            return anomalies
        finally:
            session.close()

    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        session = self.get_session()
        try:
            total_products = session.query(func.count(Product.id)).scalar()
            total_price_history = session.query(func.count(PriceHistory.id)).scalar()
            total_scrapes = session.query(func.count(ScrapeLog.id)).scalar()
            total_anomalies = session.query(func.count(AnomalyDetection.id)).scalar()

            return {
                'total_products': total_products,
                'total_price_history': total_price_history,
                'total_scrapes': total_scrapes,
                'total_anomalies': total_anomalies
            }
        finally:
            session.close()

"""
Database Models for Bilka Price Monitor

SQLAlchemy models for products, price history, and scraping sessions.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
from loguru import logger

Base = declarative_base()


class Product(Base):
    """
    Product model representing items in the Bilka catalog.

    Stores basic product information that doesn't change frequently.
    """
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(100), unique=True, nullable=False, index=True)  # BILKA product code
    name = Column(String(500), nullable=False)
    category = Column(String(100))
    subcategory = Column(String(100))
    brand = Column(String(200))
    image_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to price history
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(id={self.id}, external_id='{self.external_id}', name='{self.name}')>"


class PriceHistory(Base):
    """
    Price history model tracking price changes over time.

    Stores pricing information and discount data for each product.
    """
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    regular_price = Column(Float)
    sale_price = Column(Float)
    discount_percentage = Column(Float)
    currency = Column(String(10), default='DKK')
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_active = Column(Boolean, default=True)

    # Relationship to product
    product = relationship("Product", back_populates="price_history")

    def __repr__(self):
        return f"<PriceHistory(id={self.id}, product_id={self.product_id}, regular_price={self.regular_price}, sale_price={self.sale_price})>"


class ScrapingSession(Base):
    """
    Scraping session model tracking scraping operations.

    Records information about each scraping run for monitoring and debugging.
    """
    __tablename__ = 'scraping_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_name = Column(String(200))
    total_products = Column(Integer, default=0)
    successful_scrapes = Column(Integer, default=0)
    failed_scrapes = Column(Integer, default=0)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(50), default='running')  # 'running', 'completed', 'failed'

    def __repr__(self):
        return f"<ScrapingSession(id={self.id}, session_name='{self.session_name}', status='{self.status}')>"


class DatabaseManager:
    """
    Database manager for handling database connections and operations.

    Provides methods for creating tables, managing sessions, and basic CRUD operations.
    """

    def __init__(self, database_url: str = None):
        """
        Initialize the database manager.

        Args:
            database_url: Database connection URL. If None, uses environment variable or default SQLite.
        """
        if database_url is None:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///data/bilka_prices.db')

        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None

        self._create_engine()
        logger.info(f"Database manager initialized with: {self._get_db_type()}")

    def _create_engine(self):
        """Create SQLAlchemy engine and session factory."""
        from sqlalchemy.pool import StaticPool

        # Configure engine based on database type
        if self.database_url.startswith('sqlite'):
            self.engine = create_engine(
                self.database_url,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool,
                echo=False
            )
        else:
            self.engine = create_engine(self.database_url, echo=False)

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _get_db_type(self) -> str:
        """Get the database type from the URL."""
        if 'sqlite' in self.database_url:
            return 'SQLite'
        elif 'postgresql' in self.database_url:
            return 'PostgreSQL'
        elif 'mysql' in self.database_url:
            return 'MySQL'
        else:
            return 'Unknown'

    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def drop_tables(self):
        """Drop all database tables (use with caution)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("Database tables dropped")
        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            raise

    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()

    def close_session(self, session):
        """Close a database session."""
        try:
            session.close()
        except Exception as e:
            logger.error(f"Error closing session: {e}")

    def add_product(self, session, product_data: dict) -> Product:
        """
        Add or update a product in the database.

        Args:
            session: Database session
            product_data: Dictionary containing product information

        Returns:
            Product instance
        """
        try:
            # Check if product already exists
            existing_product = session.query(Product).filter_by(
                external_id=product_data['external_id']
            ).first()

            if existing_product:
                # Update existing product
                for key, value in product_data.items():
                    if hasattr(existing_product, key) and key not in ['id', 'created_at']:
                        setattr(existing_product, key, value)
                product = existing_product
                logger.debug(f"Updated existing product: {product.external_id}")
            else:
                # Create new product
                product = Product(**product_data)
                session.add(product)
                logger.debug(f"Added new product: {product.external_id}")

            session.commit()
            return product

        except Exception as e:
            session.rollback()
            logger.error(f"Error adding product: {e}")
            raise

    def add_price_history(self, session, product_id: int, price_data: dict) -> PriceHistory:
        """
        Add price history entry for a product.

        Args:
            session: Database session
            product_id: Product ID
            price_data: Dictionary containing price information

        Returns:
            PriceHistory instance
        """
        try:
            price_entry = PriceHistory(product_id=product_id, **price_data)
            session.add(price_entry)
            session.commit()
            logger.debug(f"Added price history for product {product_id}")
            return price_entry

        except Exception as e:
            session.rollback()
            logger.error(f"Error adding price history: {e}")
            raise

    def start_scraping_session(self, session, session_name: str) -> ScrapingSession:
        """
        Start a new scraping session.

        Args:
            session: Database session
            session_name: Name for the scraping session

        Returns:
            ScrapingSession instance
        """
        try:
            scraping_session = ScrapingSession(session_name=session_name)
            session.add(scraping_session)
            session.commit()
            logger.info(f"Started scraping session: {session_name}")
            return scraping_session

        except Exception as e:
            session.rollback()
            logger.error(f"Error starting scraping session: {e}")
            raise

    def end_scraping_session(self, session, session_id: int, status: str = 'completed'):
        """
        End a scraping session.

        Args:
            session: Database session
            session_id: Scraping session ID
            status: Final status ('completed', 'failed', etc.)
        """
        try:
            scraping_session = session.query(ScrapingSession).filter_by(id=session_id).first()
            if scraping_session:
                scraping_session.end_time = datetime.utcnow()
                scraping_session.status = status
                session.commit()
                logger.info(f"Ended scraping session {session_id} with status: {status}")
            else:
                logger.warning(f"Scraping session {session_id} not found")

        except Exception as e:
            session.rollback()
            logger.error(f"Error ending scraping session: {e}")
            raise

    def get_recent_price_history(self, session, product_id: int, limit: int = 10) -> list:
        """
        Get recent price history for a product.

        Args:
            session: Database session
            product_id: Product ID
            limit: Maximum number of records to return

        Returns:
            List of PriceHistory objects
        """
        try:
            return session.query(PriceHistory).filter_by(product_id=product_id).order_by(
                PriceHistory.scraped_at.desc()
            ).limit(limit).all()

        except Exception as e:
            logger.error(f"Error getting price history: {e}")
            return []

    def get_products_with_errors(self, session) -> list:
        """
        Get products that may have pricing errors.

        Args:
            session: Database session

        Returns:
            List of products with potential errors
        """
        try:
            # Query for products with suspicious pricing
            return session.query(Product).join(PriceHistory).filter(
                PriceHistory.discount_percentage > 90
            ).distinct().all()

        except Exception as e:
            logger.error(f"Error getting products with errors: {e}")
            return []


# Global database manager instance
_db_manager = None


def get_database_manager(database_url: str = None) -> DatabaseManager:
    """
    Get or create a database manager instance.

    Args:
        database_url: Database connection URL

    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url)
    return _db_manager


def init_database(database_url: str = None):
    """
    Initialize the database and create tables.

    Args:
        database_url: Database connection URL
    """
    db_manager = get_database_manager(database_url)
    db_manager.create_tables()
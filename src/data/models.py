"""SQLAlchemy database models for Bilka Price Monitor."""

from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Product(Base):
    """Product model for storing product information"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(255), unique=True, nullable=True, index=True)
    name = Column(String(500), nullable=False)
    brand = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True, index=True)

    # Pricing information
    current_price = Column(Float, nullable=True)
    original_price = Column(Float, nullable=True)
    discount_percentage = Column(Float, nullable=True)

    # Product details
    url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    availability = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # Metadata
    scraped_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(name='{self.name}', current_price={self.current_price})>"


class PriceHistory(Base):
    """Price history model for tracking price changes over time"""
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)

    # Price data
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    discount_percentage = Column(Float, nullable=True)

    # Timestamps
    recorded_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)

    # Relationship
    product = relationship("Product", back_populates="price_history")

    def __repr__(self):
        return f"<PriceHistory(product_id={self.product_id}, price={self.price}, recorded_at={self.recorded_at})>"


class ScrapeLog(Base):
    """Scrape log model for tracking scraping sessions"""
    __tablename__ = 'scrape_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), nullable=True)
    products_found = Column(Integer, default=0)
    products_stored = Column(Integer, default=0)
    status = Column(String(50), default='success')  # success, error, partial
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    def __repr__(self):
        return f"<ScrapeLog(category='{self.category}', status='{self.status}', products_found={self.products_found})>"


class AnomalyDetection(Base):
    """Anomaly detection model for flagging suspicious deals"""
    __tablename__ = 'anomaly_detections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)

    # Anomaly details
    anomaly_type = Column(String(100), nullable=False)  # suspicious_discount, fake_original_price, price_manipulation
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    description = Column(Text, nullable=True)

    # Supporting data
    current_price = Column(Float, nullable=True)
    historical_avg_price = Column(Float, nullable=True)
    discount_claimed = Column(Float, nullable=True)
    discount_actual = Column(Float, nullable=True)

    # Status
    verified = Column(Boolean, default=False)
    false_positive = Column(Boolean, default=False)

    # Timestamps
    detected_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    reviewed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<AnomalyDetection(product_id={self.product_id}, type='{self.anomaly_type}', confidence={self.confidence_score})>"

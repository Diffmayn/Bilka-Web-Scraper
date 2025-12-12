"""
Data processing utilities for cleaning and normalizing product data
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, UTC
import hashlib

logger = logging.getLogger(__name__)


def clean_product_data(product: Dict) -> Dict:
    """
    Clean and validate a single product's data
    
    Args:
        product: Raw product dictionary
        
    Returns:
        Cleaned product dictionary
    """
    cleaned = {}

    # Clean name
    name = product.get('name') or ''
    if name:
        cleaned['name'] = str(name).strip()[:500]  # Truncate to max length

    # Stable external id (prefer provided value, otherwise derive from URL)
    external_id = product.get('external_id') or ''
    if external_id:
        cleaned['external_id'] = str(external_id).strip()[:255]

    # Clean brand
    brand = product.get('brand') or ''
    if brand:
        cleaned['brand'] = str(brand).strip()[:255]

    # Clean category
    category = product.get('category') or ''
    if category:
        cleaned['category'] = str(category).strip()[:100]

    # Clean prices
    current_price = product.get('current_price')
    if current_price is not None and current_price >= 0:
        cleaned['current_price'] = round(float(current_price), 2)

    original_price = product.get('original_price')
    if original_price is not None and original_price >= 0:
        cleaned['original_price'] = round(float(original_price), 2)

    # Clean discount
    discount = product.get('discount_percentage')
    if discount is not None:
        cleaned['discount_percentage'] = round(float(discount), 2)

    # Clean URLs
    url = product.get('url') or ''
    if url:
        cleaned['url'] = str(url).strip()

        # If no external_id was provided, derive a stable one from the URL.
        # This avoids upserting by name (which is not stable) and reduces duplicates.
        if 'external_id' not in cleaned:
            url_hash = hashlib.sha1(cleaned['url'].encode('utf-8')).hexdigest()
            cleaned['external_id'] = url_hash[:40]

    image_url = product.get('image_url') or ''
    if image_url:
        cleaned['image_url'] = str(image_url).strip()

    # Clean availability
    availability = product.get('availability') or ''
    if availability:
        cleaned['availability'] = str(availability).strip()[:100]

    # Clean description
    description = product.get('description') or ''
    if description:
        cleaned['description'] = str(description).strip()

    # Add scraped timestamp
    scraped_at = product.get('scraped_at')
    if scraped_at is None:
        scraped_at = datetime.now(UTC)
    else:
        # Normalize naive datetimes to UTC to avoid Python 3.13 utcnow() deprecation
        try:
            if getattr(scraped_at, 'tzinfo', None) is None:
                scraped_at = scraped_at.replace(tzinfo=UTC)
        except Exception:
            scraped_at = datetime.now(UTC)

    cleaned['scraped_at'] = scraped_at

    return cleaned


def validate_product_data(product: Dict) -> tuple[bool, List[str]]:
    """
    Validate product data
    
    Args:
        product: Product dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check required fields
    if not product.get('name'):
        errors.append("Missing product name")

    # Validate prices
    current_price = product.get('current_price')
    if current_price is not None:
        if current_price < 0:
            errors.append("Current price cannot be negative")
        if current_price > 1000000:  # 1 million DKK seems unreasonable
            errors.append("Current price seems unreasonably high")

    original_price = product.get('original_price')
    if original_price is not None:
        if original_price < 0:
            errors.append("Original price cannot be negative")
        if current_price and original_price and current_price > original_price:
            errors.append("Current price higher than original price")

    # Validate discount
    discount = product.get('discount_percentage')
    if discount is not None:
        if discount < 0 or discount > 100:
            errors.append("Discount percentage must be between 0 and 100")

    is_valid = len(errors) == 0
    return is_valid, errors


def process_products(products: List[Dict]) -> List[Dict]:
    """
    Process a list of products (clean and validate)
    
    Args:
        products: List of raw product dictionaries
        
    Returns:
        List of cleaned and validated product dictionaries
    """
    processed = []

    for product in products:
        # Clean the data
        cleaned = clean_product_data(product)

        # Validate the data
        is_valid, errors = validate_product_data(cleaned)

        if is_valid:
            processed.append(cleaned)
        else:
            logger.warning(f"Invalid product data for '{cleaned.get('name', 'Unknown')}': {errors}")
            # Still add it but log the issues
            processed.append(cleaned)

    logger.info(f"Processed {len(processed)}/{len(products)} products")
    return processed


def normalize_price(price: float, currency: str = 'DKK') -> float:
    """
    Normalize price to a standard format
    
    Args:
        price: Price value
        currency: Currency code
        
    Returns:
        Normalized price
    """
    # For now, just round to 2 decimals
    # In future, could add currency conversion
    return round(price, 2)


def calculate_actual_discount(current_price: float, original_price: float) -> Optional[float]:
    """
    Calculate actual discount percentage
    
    Args:
        current_price: Current/sale price
        original_price: Original price
        
    Returns:
        Discount percentage or None if invalid
    """
    if not original_price or original_price <= 0:
        return None

    if not current_price or current_price < 0:
        return None

    if current_price > original_price:
        return None  # Not actually a discount

    discount = ((original_price - current_price) / original_price) * 100
    return round(discount, 2)

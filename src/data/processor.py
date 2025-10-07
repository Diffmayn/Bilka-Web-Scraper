"""
Data processing utilities for cleaning and normalizing product data
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

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
    name = product.get('name', '').strip()
    if name:
        cleaned['name'] = name[:500]  # Truncate to max length

    # Clean brand
    brand = product.get('brand', '').strip()
    if brand:
        cleaned['brand'] = brand[:255]

    # Clean category
    category = product.get('category', '').strip()
    if category:
        cleaned['category'] = category[:100]

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
    url = product.get('url', '').strip()
    if url:
        cleaned['url'] = url

    image_url = product.get('image_url', '').strip()
    if image_url:
        cleaned['image_url'] = image_url

    # Clean availability
    availability = product.get('availability', '').strip()
    if availability:
        cleaned['availability'] = availability[:100]

    # Clean description
    description = product.get('description', '').strip()
    if description:
        cleaned['description'] = description

    # Add scraped timestamp
    cleaned['scraped_at'] = product.get('scraped_at', datetime.utcnow())

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

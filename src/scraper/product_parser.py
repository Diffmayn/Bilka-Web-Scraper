"""
Product Parser for extracting product data from HTML
"""

import re
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class ProductParser:
    """Parses product data from Bilka.dk HTML"""

    def __init__(self, selectors: Optional[Dict] = None):
        self.selectors = selectors or self._default_selectors()

    def _default_selectors(self) -> Dict:
        """Default CSS selectors for Bilka.dk"""
        return {
            'product_container': '.product-card',
            'product_name': '.v-card__title',
            'price_regular': '.after-price',
            'price_sale': '.price-sale',
            'discount_badge': '.discount-percentage',
            'product_image': '.product-image img',
            'product_url': '.product-card',
            'availability': '.stock-status',
            'brand': '.product-brand',
        }

    def parse_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None

        try:
            # Remove currency symbols and extract numbers
            price_match = re.search(r'(\d+[,.]?\d{0,2})', price_text.replace(' ', ''))
            if price_match:
                price_str = price_match.group(1).replace(',', '.')
                return float(price_str)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse price '{price_text}': {e}")

        return None

    def parse_discount(self, discount_text: str) -> Optional[float]:
        """Extract discount percentage from text"""
        if not discount_text:
            return None

        try:
            discount_match = re.search(r'(-?\d+)%?', discount_text)
            if discount_match:
                return abs(float(discount_match.group(1)))
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse discount '{discount_text}': {e}")

        return None

    def parse_product(self, element: BeautifulSoup) -> Optional[Dict]:
        """Parse a single product element"""
        try:
            # Extract product name
            name_elem = element.select_one(self.selectors['product_name'])
            name = name_elem.get_text(strip=True) if name_elem else None

            if not name:
                return None

            # Extract prices
            price_regular_elem = element.select_one(self.selectors['price_regular'])
            price_sale_elem = element.select_one(self.selectors['price_sale'])

            regular_price = self.parse_price(
                price_regular_elem.get_text(strip=True) if price_regular_elem else None
            )
            sale_price = self.parse_price(
                price_sale_elem.get_text(strip=True) if price_sale_elem else None
            )

            # Current price is sale price if available, otherwise regular price
            current_price = sale_price if sale_price else regular_price
            original_price = regular_price if sale_price else None

            # Extract discount
            discount_elem = element.select_one(self.selectors['discount_badge'])
            discount_percentage = None
            if discount_elem:
                discount_percentage = self.parse_discount(discount_elem.get_text(strip=True))
            elif sale_price and regular_price and regular_price > 0:
                # Calculate discount if not explicitly shown
                discount_percentage = ((regular_price - sale_price) / regular_price) * 100

            # Extract URL
            url_elem = element.select_one(self.selectors['product_url'])
            url = url_elem.get('href') if url_elem and url_elem.has_attr('href') else None

            # Extract image
            image_elem = element.select_one(self.selectors['product_image'])
            image_url = image_elem.get('src') if image_elem and image_elem.has_attr('src') else None

            # Extract brand
            brand_elem = element.select_one(self.selectors['brand'])
            brand = brand_elem.get_text(strip=True) if brand_elem else None

            # Extract availability
            avail_elem = element.select_one(self.selectors['availability'])
            availability = avail_elem.get_text(strip=True) if avail_elem else None

            return {
                'name': name,
                'current_price': current_price,
                'original_price': original_price,
                'discount_percentage': discount_percentage,
                'url': url,
                'image_url': image_url,
                'brand': brand,
                'availability': availability,
            }

        except Exception as e:
            logger.warning(f"Failed to parse product element: {e}")
            return None

    def parse_products(self, html: str) -> List[Dict]:
        """Parse multiple products from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        product_elements = soup.select(self.selectors['product_container'])

        products = []
        for element in product_elements:
            product = self.parse_product(element)
            if product:
                products.append(product)

        logger.info(f"Parsed {len(products)} products from HTML")
        return products

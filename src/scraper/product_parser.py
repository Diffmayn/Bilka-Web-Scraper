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
            'product_container': 'a.product-card',
            'product_name': '.v-card__title',
            'product_description': '.description-text',
            'price_before': '.before-price .amount',
            'price_current': '.price-text .amount',
            'discount_badge': '.sticker__promotionSaving',
            'product_image': '.v-image__image',
            'product_url': 'a.product-card',
            'availability': '.text-right',
            'store_stock': '.store-stock',
            'brand': '.product-brand',
        }

    def parse_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text (handles Danish format like '7.499,-')"""
        if not price_text:
            return None

        try:
            # Remove common text like "Før", "Plus evt. fragt", "kr", "DKK", etc.
            price_text = price_text.replace('Før', '').replace('Plus evt. fragt', '')
            price_text = price_text.replace('kr', '').replace('DKK', '').replace(',-', '')
            price_text = price_text.strip()
            
            # Danish format uses dot as thousand separator: 7.499 = 7499
            # Remove dots used as thousand separators
            price_text = price_text.replace('.', '')
            
            # Handle comma as decimal separator (7,50 = 7.50)
            price_text = price_text.replace(',', '.')
            
            # Extract just the numbers
            price_match = re.search(r'(\d+\.?\d{0,2})', price_text)
            if price_match:
                return float(price_match.group(1))
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse price '{price_text}': {e}")

        return None

    def parse_discount(self, discount_text: str) -> Optional[float]:
        """Extract discount percentage from text (handles 'Spar 40%' format)"""
        if not discount_text:
            return None

        try:
            # Handle Danish "Spar X%" format or just "X%"
            discount_text = discount_text.replace('Spar', '').replace('spar', '').strip()
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

            # Extract prices - Bilka shows "Før X,-" (before) and current price
            price_before_elem = element.select_one(self.selectors['price_before'])
            price_current_elem = element.select_one(self.selectors['price_current'])

            # Parse before price (original price)
            original_price = None
            if price_before_elem:
                original_price = self.parse_price(price_before_elem.get_text(strip=True))

            # Parse current price
            current_price = None
            if price_current_elem:
                current_price = self.parse_price(price_current_elem.get_text(strip=True))
            
            # If no current price found but we have original price, current = original (no discount)
            if not current_price and original_price:
                current_price = original_price
                original_price = None

            # Extract discount from badge
            discount_elem = element.select_one(self.selectors['discount_badge'])
            discount_percentage = None
            if discount_elem:
                # Extract text like "Spar 40%"
                discount_text = discount_elem.get_text(strip=True)
                discount_percentage = self.parse_discount(discount_text)
            elif current_price and original_price and original_price > 0:
                # Calculate discount if not explicitly shown
                discount_percentage = ((original_price - current_price) / original_price) * 100

            # Extract URL - the element itself is an <a> tag
            url = element.get('href') if element.has_attr('href') else None
            if url and not url.startswith('http'):
                url = f"https://www.bilka.dk{url}"

            # Extract image
            image_elem = element.select_one(self.selectors['product_image'])
            image_url = None
            if image_elem:
                # Check for style background-image or src
                if image_elem.has_attr('style'):
                    style = image_elem.get('style', '')
                    import re
                    match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                    if match:
                        image_url = match.group(1)
                elif image_elem.name == 'img' and image_elem.has_attr('src'):
                    image_url = image_elem.get('src')

            # Extract brand (may not always be present)
            brand_elem = element.select_one(self.selectors['brand'])
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            
            # Extract brand from product name if not found
            if not brand and name:
                # First word is usually the brand
                brand = name.split()[0] if ' ' in name else None

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
        logger.info(f"Parsing HTML of length {len(html)}")
        logger.info(f"Using selector: {self.selectors['product_container']}")
        
        soup = BeautifulSoup(html, 'html.parser')
        product_elements = soup.select(self.selectors['product_container'])
        
        logger.info(f"Found {len(product_elements)} product elements with selector '{self.selectors['product_container']}'")
        
        # Debug: Try alternative selectors if main one fails
        if len(product_elements) == 0:
            logger.error("No products found with main selector, trying alternatives...")
            
            # Try just .product-card
            alt1 = soup.select('.product-card')
            logger.error(f"DEBUG: Found {len(alt1)} elements with '.product-card'")
            
            # Try a[class*="product"]
            alt2 = soup.select('a[class*="product"]')
            logger.error(f"DEBUG: Found {len(alt2)} elements with 'a[class*=\"product\"]'")
            
            # Try all <a> tags
            alt3 = soup.select('a')
            logger.error(f"DEBUG: Found {len(alt3)} total <a> tags")
            
            # Save snippet of HTML for debugging
            if len(html) > 0:
                logger.error(f"DEBUG: HTML snippet (first 1000 chars):\n{html[:1000]}")

        products = []
        for idx, element in enumerate(product_elements):
            logger.debug(f"Parsing product {idx + 1}/{len(product_elements)}")
            product = self.parse_product(element)
            if product:
                products.append(product)
                logger.debug(f"Successfully parsed: {product.get('name', 'Unknown')[:50]}")
            else:
                logger.debug(f"Failed to parse product {idx + 1}")

        logger.info(f"Successfully parsed {len(products)} valid products from {len(product_elements)} elements")
        return products

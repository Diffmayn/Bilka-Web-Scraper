"""
Product Parser for Bilka Price Monitor

Extracts product information from HTML content using BeautifulSoup.
Handles various price formats, discount calculations, and data validation.
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup
import yaml
from loguru import logger


@dataclass
class ProductData:
    """Data class for parsed product information."""
    external_id: str
    name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    regular_price: Optional[float] = None
    sale_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    currency: str = "DKK"
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    availability: Optional[str] = None
    scraped_at: Optional[str] = None


class PriceFormatError(Exception):
    """Exception raised when price format cannot be parsed."""
    pass


class ProductNotFoundError(Exception):
    """Exception raised when product data cannot be found."""
    pass


class ProductParser:
    """
    Parser for extracting product data from Bilka.dk HTML content.

    Handles various price formats, discount calculations, and data validation.
    """

    def __init__(self, rules_path: str = "config/scraping_rules.yaml"):
        """
        Initialize the product parser.

        Args:
            rules_path: Path to the scraping rules YAML file
        """
        self.rules = self._load_rules(rules_path)
        self.selectors = self.rules.get('selectors', {})
        self.patterns = self.rules.get('patterns', {})
        self.validation = self.rules.get('validation', {})

        logger.info("Product Parser initialized")

    def _load_rules(self, rules_path: str) -> Dict[str, Any]:
        """Load scraping rules from YAML file."""
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Rules file {rules_path} not found, using defaults")
            return self._get_default_rules()
        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            return self._get_default_rules()

    def _get_default_rules(self) -> Dict[str, Any]:
        """Return default scraping rules."""
        return {
            'selectors': {
                'product_container': '.product-grid-item',
                'product_name': '.product-title a',
                'price_regular': '.price-regular',
                'price_sale': '.price-sale',
                'discount_badge': '.discount-percentage',
                'product_image': '.product-image img',
                'product_url': '.product-title a',
                'availability': '.stock-status'
            },
            'patterns': {
                'price_regex': r'(\d+[,.]\d{2})',
                'discount_regex': r'(-?\d+)',
                'currency': r'kr\.|DKK'
            },
            'validation': {
                'max_price': 100000,
                'min_price': 0.01,
                'max_discount': 95
            }
        }

    def parse_product(self, html_content: str, base_url: str = "https://bilka.dk") -> ProductData:
        """
        Parse product data from HTML content.

        Args:
            html_content: HTML content containing product information
            base_url: Base URL for constructing absolute URLs

        Returns:
            ProductData object with parsed information

        Raises:
            ProductNotFoundError: If essential product data cannot be found
            PriceFormatError: If price format cannot be parsed
        """
        soup = BeautifulSoup(html_content, 'lxml')

        # Extract basic product information
        external_id = self._extract_external_id(soup)
        name = self._extract_product_name(soup)
        product_url = self._extract_product_url(soup, base_url)
        image_url = self._extract_image_url(soup, base_url)

        if not name:
            raise ProductNotFoundError("Product name not found")

        # Extract pricing information
        regular_price = self._extract_price(soup, 'price_regular')
        sale_price = self._extract_price(soup, 'price_sale')
        discount_percentage = self._extract_discount_percentage(soup)

        # Extract additional information
        category = self._extract_category(soup)
        brand = self._extract_brand(soup)
        availability = self._extract_availability(soup)

        # Validate and calculate discount if not provided
        if discount_percentage is None and regular_price and sale_price:
            discount_percentage = self._calculate_discount_percentage(regular_price, sale_price)

        # Validate data
        self._validate_product_data(regular_price, sale_price, discount_percentage)

        return ProductData(
            external_id=external_id or self._generate_external_id(name),
            name=name,
            category=category,
            brand=brand,
            regular_price=regular_price,
            sale_price=sale_price,
            discount_percentage=discount_percentage,
            image_url=image_url,
            product_url=product_url,
            availability=availability
        )

    def parse_multiple_products(self, html_content: str, base_url: str = "https://bilka.dk") -> List[ProductData]:
        """
        Parse multiple products from a page containing product listings.

        Args:
            html_content: HTML content containing multiple products
            base_url: Base URL for constructing absolute URLs

        Returns:
            List of ProductData objects
        """
        soup = BeautifulSoup(html_content, 'lxml')
        products = []

        # Find all product containers
        product_containers = soup.select(self.selectors.get('product_container', '.product-grid-item'))

        for container in product_containers:
            try:
                product_html = str(container)
                product_data = self.parse_product(product_html, base_url)
                products.append(product_data)
            except (ProductNotFoundError, PriceFormatError) as e:
                logger.debug(f"Skipping product: {e}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected error parsing product: {e}")
                continue

        logger.info(f"Parsed {len(products)} products from page")
        return products

    def _extract_product_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product name from HTML."""
        try:
            name_element = soup.select_one(self.selectors.get('product_name', '.product-title a'))
            if name_element:
                return name_element.get_text(strip=True)
        except Exception as e:
            logger.debug(f"Error extracting product name: {e}")
        return None

    def _extract_external_id(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract external product ID from HTML."""
        try:
            # Try to extract from URL or data attributes
            url_element = soup.select_one(self.selectors.get('product_url', '.product-title a'))
            if url_element and url_element.get('href'):
                href = url_element['href']
                # Extract ID from URL pattern like /product/12345
                match = re.search(r'/product/(\d+)', href)
                if match:
                    return match.group(1)
        except Exception as e:
            logger.debug(f"Error extracting external ID: {e}")
        return None

    def _extract_product_url(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract product URL from HTML."""
        try:
            url_element = soup.select_one(self.selectors.get('product_url', '.product-title a'))
            if url_element and url_element.get('href'):
                href = url_element['href']
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return f"{base_url}{href}"
        except Exception as e:
            logger.debug(f"Error extracting product URL: {e}")
        return None

    def _extract_image_url(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract product image URL from HTML."""
        try:
            img_element = soup.select_one(self.selectors.get('product_image', '.product-image img'))
            if img_element and img_element.get('src'):
                src = img_element['src']
                if src.startswith('http'):
                    return src
                elif src.startswith('/'):
                    return f"{base_url}{src}"
        except Exception as e:
            logger.debug(f"Error extracting image URL: {e}")
        return None

    def _extract_price(self, soup: BeautifulSoup, price_type: str) -> Optional[float]:
        """Extract price from HTML based on type (regular or sale)."""
        try:
            selector = self.selectors.get(price_type)
            if not selector:
                return None

            price_element = soup.select_one(selector)
            if not price_element:
                return None

            price_text = price_element.get_text(strip=True)

            # Extract numeric price using regex
            price_match = re.search(self.patterns.get('price_regex', r'(\d+[,.]\d{2})'), price_text)
            if price_match:
                price_str = price_match.group(1).replace(',', '.')
                return float(price_str)

        except Exception as e:
            logger.debug(f"Error extracting {price_type}: {e}")
        return None

    def _extract_discount_percentage(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract discount percentage from HTML."""
        try:
            discount_element = soup.select_one(self.selectors.get('discount_badge', '.discount-percentage'))
            if discount_element:
                discount_text = discount_element.get_text(strip=True)

                # Extract percentage using regex
                discount_match = re.search(self.patterns.get('discount_regex', r'(-?\d+)'), discount_text)
                if discount_match:
                    return float(discount_match.group(1))

        except Exception as e:
            logger.debug(f"Error extracting discount percentage: {e}")
        return None

    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product category from HTML."""
        try:
            # Try breadcrumb navigation
            breadcrumb = soup.select_one(self.selectors.get('category_breadcrumb', '.breadcrumb'))
            if breadcrumb:
                categories = breadcrumb.select('a')
                if len(categories) >= 2:  # Skip home link
                    return categories[-1].get_text(strip=True)
        except Exception as e:
            logger.debug(f"Error extracting category: {e}")
        return None

    def _extract_brand(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product brand from HTML."""
        try:
            brand_element = soup.select_one(self.selectors.get('brand', '.product-brand'))
            if brand_element:
                return brand_element.get_text(strip=True)
        except Exception as e:
            logger.debug(f"Error extracting brand: {e}")
        return None

    def _extract_availability(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product availability from HTML."""
        try:
            availability_element = soup.select_one(self.selectors.get('availability', '.stock-status'))
            if availability_element:
                return availability_element.get_text(strip=True)
        except Exception as e:
            logger.debug(f"Error extracting availability: {e}")
        return None

    def _calculate_discount_percentage(self, regular_price: float, sale_price: float) -> Optional[float]:
        """Calculate discount percentage from regular and sale prices."""
        try:
            if regular_price > 0 and sale_price >= 0:
                if sale_price <= regular_price:
                    return round(((regular_price - sale_price) / regular_price) * 100, 2)
                else:
                    # Sale price higher than regular - invalid
                    return None
        except Exception as e:
            logger.debug(f"Error calculating discount: {e}")
        return None

    def _generate_external_id(self, product_name: str) -> str:
        """Generate a fallback external ID from product name."""
        # Create a simple hash-like ID from product name
        import hashlib
        name_hash = hashlib.md5(product_name.encode('utf-8')).hexdigest()[:8]
        return f"generated_{name_hash}"

    def _validate_product_data(self, regular_price: Optional[float],
                             sale_price: Optional[float],
                             discount_percentage: Optional[float]) -> None:
        """Validate parsed product data."""
        max_price = self.validation.get('max_price', 100000)
        min_price = self.validation.get('min_price', 0.01)
        max_discount = self.validation.get('max_discount', 95)

        # Validate price ranges
        for price, price_type in [(regular_price, 'regular'), (sale_price, 'sale')]:
            if price is not None:
                if price < min_price or price > max_price:
                    raise PriceFormatError(f"Invalid {price_type} price: {price}")

        # Validate discount percentage
        if discount_percentage is not None:
            if discount_percentage < -50 or discount_percentage > max_discount:  # Allow some negative for errors
                logger.warning(f"Suspicious discount percentage: {discount_percentage}%")

        # Validate price relationships
        if regular_price is not None and sale_price is not None:
            if sale_price > regular_price:
                logger.warning(f"Sale price ({sale_price}) higher than regular price ({regular_price})")


# Convenience function for quick parsing
def parse_product_html(html_content: str, base_url: str = "https://bilka.dk") -> ProductData:
    """
    Convenience function to parse a single product from HTML.

    Args:
        html_content: HTML content containing product information
        base_url: Base URL for constructing absolute URLs

    Returns:
        ProductData object with parsed information
    """
    parser = ProductParser()
    return parser.parse_product(html_content, base_url)
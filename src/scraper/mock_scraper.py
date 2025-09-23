"""
Mock Scraper for Bilka Price Monitor

Simulates web scraping functionality for testing purposes.
Generates realistic sample data to test the application pipeline.
"""

import random
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import yaml
from loguru import logger

from src.scraper.product_parser import ProductData


@dataclass
class MockScrapingResult:
    """Result of mock scraping operation."""
    products: List[ProductData]
    category: str
    success: bool
    duration: float
    error_message: Optional[str] = None


class MockBilkaScraper:
    """
    Mock scraper that simulates BILKA.dk scraping without actual web requests.

    Generates realistic sample data for testing the application pipeline.
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        Initialize the mock scraper.

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.categories = {
            'electronics': ['Smartphones', 'Laptops', 'Tablets', 'Headphones', 'Smart Watches'],
            'home': ['Coffee Machines', 'Blenders', 'Vacuum Cleaners', 'Air Fryers', 'Washing Machines'],
            'fashion': ['T-Shirts', 'Jeans', 'Sneakers', 'Jackets', 'Watches'],
            'sports': ['Running Shoes', 'Yoga Mats', 'Dumbbells', 'Treadmills', 'Bicycles']
        }
        self.brands = ['Samsung', 'Apple', 'Sony', 'Nike', 'Adidas', 'Bosch', 'Philips', 'LG', 'Huawei', 'Dell']

        logger.info("Mock Bilka Scraper initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'scraping': {
                'request_delay_min': 1,
                'request_delay_max': 3,
                'max_retries': 3
            }
        }

    def scrape_category(self, category: str, max_products: int = 50) -> List[ProductData]:
        """
        Simulate scraping a product category.

        Args:
            category: Category to scrape
            max_products: Maximum number of products to generate

        Returns:
            List of ProductData objects
        """
        logger.info(f"Starting mock scrape for category: {category}")

        start_time = time.time()

        try:
            # Simulate network delay
            delay = random.uniform(
                self.config['scraping']['request_delay_min'],
                self.config['scraping']['request_delay_max']
            )
            time.sleep(delay)

            # Generate mock products
            products = self._generate_mock_products(category, max_products)

            duration = time.time() - start_time
            logger.info(f"Mock scraped {len(products)} products from {category} in {duration:.2f}s")

            return products

        except Exception as e:
            logger.error(f"Error in mock scraping: {e}")
            return []

    def scrape_all_categories(self, max_products_per_category: int = 20) -> Dict[str, List[ProductData]]:
        """
        Simulate scraping all categories.

        Args:
            max_products_per_category: Max products per category

        Returns:
            Dictionary mapping categories to product lists
        """
        logger.info("Starting mock scrape for all categories")

        results = {}
        for category in self.categories.keys():
            products = self.scrape_category(category, max_products_per_category)
            results[category] = products

        total_products = sum(len(products) for products in results.values())
        logger.info(f"Mock scraped {total_products} products across {len(results)} categories")

        return results

    def _generate_mock_products(self, category: str, count: int) -> List[ProductData]:
        """
        Generate mock product data for a category.

        Args:
            category: Product category
            count: Number of products to generate

        Returns:
            List of ProductData objects
        """
        products = []
        product_names = self.categories.get(category, ['Generic Product'])

        for i in range(count):
            # Generate realistic product data
            product_name = self._generate_product_name(product_names, i)
            brand = random.choice(self.brands)
            full_name = f"{brand} {product_name}"

            # Generate pricing with some realistic variations
            base_price = self._get_base_price_for_category(category)
            regular_price = round(base_price * random.uniform(0.8, 1.5), 2)
            discount_percentage = random.randint(0, 70) if random.random() < 0.7 else 0

            if discount_percentage > 0:
                sale_price = round(regular_price * (1 - discount_percentage / 100), 2)
            else:
                sale_price = None

            # Generate external ID
            external_id = f"{category.upper()}_{brand.upper()}_{i:04d}"

            # Create product data
            product = ProductData(
                external_id=external_id,
                name=full_name,
                category=category,
                subcategory=random.choice(product_names),
                brand=brand,
                regular_price=regular_price,
                sale_price=sale_price,
                discount_percentage=discount_percentage if discount_percentage > 0 else None,
                currency="DKK",
                image_url=f"https://example.com/images/{external_id}.jpg",
                product_url=f"https://bilka.dk/product/{external_id}",
                availability=random.choice(["In Stock", "Limited Stock", "Out of Stock"]),
                scraped_at=datetime.now().isoformat()
            )

            products.append(product)

        return products

    def _generate_product_name(self, product_names: List[str], index: int) -> str:
        """Generate a product name from available options."""
        base_name = random.choice(product_names)

        # Add some variation
        variations = ['', ' Pro', ' Plus', ' Max', ' Mini', ' XL', ' S', ' M', ' L']
        variation = random.choice(variations)

        # Add model number
        if random.random() < 0.5:
            model = f" {random.randint(100, 9999)}"
        else:
            model = ""

        return f"{base_name}{variation}{model}"

    def _get_base_price_for_category(self, category: str) -> float:
        """Get base price range for a category."""
        price_ranges = {
            'electronics': (500, 15000),    # Smartphones, laptops, etc.
            'home': (200, 5000),           # Appliances, furniture
            'fashion': (50, 2000),         # Clothing, accessories
            'sports': (100, 3000)          # Sports equipment
        }

        min_price, max_price = price_ranges.get(category, (100, 1000))
        return random.uniform(min_price, max_price)

    def get_scraping_stats(self) -> Dict[str, Any]:
        """
        Get mock scraping statistics.

        Returns:
            Dictionary with scraping statistics
        """
        return {
            'total_categories': len(self.categories),
            'total_product_types': sum(len(products) for products in self.categories.values()),
            'estimated_products': sum(len(products) * 50 for products in self.categories.values()),
            'mock_mode': True,
            'last_updated': datetime.now().isoformat()
        }


# Convenience functions
def create_mock_scraper(config_path: str = "config/settings.yaml") -> MockBilkaScraper:
    """
    Create a mock scraper instance.

    Args:
        config_path: Path to configuration file

    Returns:
        MockBilkaScraper instance
    """
    return MockBilkaScraper(config_path)


def simulate_scraping_session(category: str = "electronics", max_products: int = 10) -> MockScrapingResult:
    """
    Simulate a complete scraping session.

    Args:
        category: Category to scrape
        max_products: Maximum products to generate

    Returns:
        MockScrapingResult with session details
    """
    scraper = MockBilkaScraper()
    start_time = time.time()

    try:
        products = scraper.scrape_category(category, max_products)
        duration = time.time() - start_time

        return MockScrapingResult(
            products=products,
            category=category,
            success=True,
            duration=duration
        )

    except Exception as e:
        duration = time.time() - start_time
        return MockScrapingResult(
            products=[],
            category=category,
            success=False,
            duration=duration,
            error_message=str(e)
        )
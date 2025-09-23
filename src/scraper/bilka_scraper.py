"""
Main Scraper for Bilka Price Monitor

Orchestrates the scraping process using SessionManager and ProductParser.
Handles category navigation, pagination, and data collection.
"""

import time
from typing import List, Dict, Optional, Any
from datetime import datetime
import yaml
from loguru import logger

from .session_manager import SessionManager, ScrapingError
from .product_parser import ProductParser, ProductData, ProductNotFoundError


class BilkaScraper:
    """
    Main scraper class for Bilka.dk product data collection.

    Coordinates session management, product parsing, and data collection
    across different categories and pages.
    """

    def __init__(self, config_path: str = "config/settings.yaml",
                 rules_path: str = "config/scraping_rules.yaml"):
        """
        Initialize the Bilka scraper.

        Args:
            config_path: Path to the configuration YAML file
            rules_path: Path to the scraping rules YAML file
        """
        self.config = self._load_config(config_path)
        self.session_manager = SessionManager(config_path)
        self.product_parser = ProductParser(rules_path)

        self.base_url = self.config.get('bilka', {}).get('base_url', 'https://bilka.dk')
        self.categories = self.config.get('bilka', {}).get('categories', {})

        logger.info("Bilka Scraper initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'bilka': {
                'base_url': 'https://bilka.dk',
                'categories': {
                    'electronics': '/elektronik',
                    'home': '/hjem-og-interior',
                    'fashion': '/mode',
                    'sports': '/sport-og-fritid'
                }
            },
            'scraping': {
                'request_delay_min': 2,
                'request_delay_max': 5,
                'max_retries': 3
            }
        }

    def scrape_category(self, category: str, max_products: int = 100) -> List[ProductData]:
        """
        Scrape products from a specific category.

        Args:
            category: Category name (must be in config)
            max_products: Maximum number of products to scrape

        Returns:
            List of ProductData objects

        Raises:
            ValueError: If category is not configured
        """
        if category not in self.categories:
            available_categories = list(self.categories.keys())
            raise ValueError(f"Category '{category}' not found. Available: {available_categories}")

        logger.info(f"Starting scrape for category: {category}")

        products = []
        category_url = f"{self.base_url}{self.categories[category]}"

        try:
            with self.session_manager:
                # Navigate to category page
                if not self.session_manager.navigate_to_url(category_url):
                    logger.error(f"Failed to navigate to category: {category}")
                    return products

                # Scrape products from the category
                page_products = self._scrape_category_page(max_products)
                products.extend(page_products)

                logger.info(f"Scraped {len(products)} products from category: {category}")

        except Exception as e:
            logger.error(f"Error scraping category {category}: {e}")

        return products

    def scrape_all_categories(self, max_products_per_category: int = 100) -> Dict[str, List[ProductData]]:
        """
        Scrape products from all configured categories.

        Args:
            max_products_per_category: Maximum products per category

        Returns:
            Dictionary mapping category names to product lists
        """
        results = {}

        for category in self.categories.keys():
            try:
                products = self.scrape_category(category, max_products_per_category)
                results[category] = products
                logger.info(f"Completed scraping category: {category} ({len(products)} products)")
            except Exception as e:
                logger.error(f"Failed to scrape category {category}: {e}")
                results[category] = []

        total_products = sum(len(products) for products in results.values())
        logger.info(f"Total products scraped: {total_products}")

        return results

    def _scrape_category_page(self, max_products: int) -> List[ProductData]:
        """
        Scrape products from the current category page.

        Args:
            max_products: Maximum number of products to scrape

        Returns:
            List of ProductData objects
        """
        products = []
        page_num = 1

        while len(products) < max_products:
            logger.debug(f"Scraping page {page_num}")

            # Get page source
            page_source = self.session_manager.get_page_source()

            # Parse products from current page
            page_products = self.product_parser.parse_multiple_products(page_source, self.base_url)

            if not page_products:
                logger.debug("No products found on current page")
                break

            # Add timestamp to products
            timestamp = datetime.now().isoformat()
            for product in page_products:
                product.scraped_at = timestamp

            products.extend(page_products)

            # Check if we have enough products
            if len(products) >= max_products:
                products = products[:max_products]
                break

            # Try to navigate to next page
            if not self._navigate_to_next_page():
                logger.debug("No more pages available")
                break

            page_num += 1

            # Add delay between pages
            delay = self.config['scraping']['request_delay_max']
            time.sleep(delay)

        return products

    def _navigate_to_next_page(self) -> bool:
        """
        Navigate to the next page of products.

        Returns:
            True if navigation successful, False otherwise
        """
        try:
            # Common pagination selectors
            next_selectors = [
                '.pagination .next',
                '.pagination-next',
                'a[rel="next"]',
                '.next-page',
                'button[data-page]'
            ]

            for selector in next_selectors:
                try:
                    next_button = self.session_manager.driver.find_element('css_selector', selector)
                    if next_button.is_displayed() and next_button.is_enabled():
                        next_button.click()
                        time.sleep(2)  # Wait for page load
                        return True
                except Exception:
                    continue

            # Try URL-based pagination
            current_url = self.session_manager.driver.current_url
            if 'page=' in current_url:
                # Extract current page number
                import re
                page_match = re.search(r'page=(\d+)', current_url)
                if page_match:
                    current_page = int(page_match.group(1))
                    next_url = re.sub(r'page=\d+', f'page={current_page + 1}', current_url)
                    return self.session_manager.navigate_to_url(next_url)

        except Exception as e:
            logger.debug(f"Error navigating to next page: {e}")

        return False

    def scrape_single_product(self, product_url: str) -> Optional[ProductData]:
        """
        Scrape data for a single product from its URL.

        Args:
            product_url: Full URL to the product page

        Returns:
            ProductData object or None if scraping failed
        """
        try:
            with self.session_manager:
                if not self.session_manager.navigate_to_url(product_url):
                    logger.error(f"Failed to navigate to product: {product_url}")
                    return None

                # Get page source
                page_source = self.session_manager.get_page_source()

                # Parse product data
                product_data = self.product_parser.parse_product(page_source, self.base_url)
                product_data.scraped_at = datetime.now().isoformat()
                product_data.product_url = product_url

                logger.info(f"Successfully scraped product: {product_data.name}")
                return product_data

        except (ProductNotFoundError, ScrapingError) as e:
            logger.warning(f"Failed to scrape product {product_url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error scraping product {product_url}: {e}")

        return None

    def get_category_info(self) -> Dict[str, str]:
        """
        Get information about available categories.

        Returns:
            Dictionary mapping category names to their URLs
        """
        return {
            name: f"{self.base_url}{path}"
            for name, path in self.categories.items()
        }

    def test_connection(self) -> bool:
        """
        Test connection to Bilka.dk and basic scraping functionality.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.session_manager:
                success = self.session_manager.navigate_to_url(self.base_url)
                if success:
                    logger.info("Connection test successful")
                    return True
                else:
                    logger.error("Connection test failed")
                    return False
        except Exception as e:
            logger.error(f"Connection test error: {e}")
            return False


# Convenience functions for quick scraping
def scrape_bilka_category(category: str, max_products: int = 100) -> List[ProductData]:
    """
    Convenience function to scrape a specific category.

    Args:
        category: Category name
        max_products: Maximum number of products to scrape

    Returns:
        List of ProductData objects
    """
    scraper = BilkaScraper()
    return scraper.scrape_category(category, max_products)


def scrape_all_bilka_categories(max_products_per_category: int = 100) -> Dict[str, List[ProductData]]:
    """
    Convenience function to scrape all categories.

    Args:
        max_products_per_category: Maximum products per category

    Returns:
        Dictionary mapping category names to product lists
    """
    scraper = BilkaScraper()
    return scraper.scrape_all_categories(max_products_per_category)
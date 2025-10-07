"""
Bilka.dk Web Scraper
Main scraping engine with support for multiple categories
"""

import yaml
import logging
import random
import time
from typing import Dict, List, Optional
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .session_manager import SessionManager
from .product_parser import ProductParser

logger = logging.getLogger(__name__)


class BilkaScraper:
    """Main scraper class for Bilka.dk"""

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.base_url = self.config.get('bilka', {}).get('base_url', 'https://bilka.dk')
        self.categories = self.config.get('bilka', {}).get('categories', {})

        # Load scraping rules
        rules_path = Path(config_path).parent / "scraping_rules.yaml"
        self.rules = self._load_rules(rules_path)

        # Initialize components
        scraping_config = self.config.get('scraping', {})
        self.session_manager = SessionManager(
            headless=scraping_config.get('headless', True)
        )
        self.parser = ProductParser(self.rules.get('selectors', {}))

        self.max_retries = scraping_config.get('max_retries', 3)
        self.timeout = scraping_config.get('timeout', 30)
        self.delay_min = scraping_config.get('request_delay_min', 2)
        self.delay_max = scraping_config.get('request_delay_max', 5)

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {}

    def _load_rules(self, rules_path: Path) -> Dict:
        """Load scraping rules from YAML file"""
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"Rules file not found: {rules_path}, using defaults")
            return {}

    def _random_delay(self):
        """Add random delay between requests"""
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)

    def scrape_category(self, category: str, max_products: int = 100) -> List[Dict]:
        """
        Scrape products from a specific category
        
        Args:
            category: Category name (electronics, home, fashion, sports)
            max_products: Maximum number of products to scrape
            
        Returns:
            List of product dictionaries
        """
        logger.info(f"Starting scrape for category: {category}")

        # Get category URL
        category_path = self.categories.get(category)
        if not category_path:
            logger.error(f"Unknown category: {category}")
            logger.error(f"Available categories: {list(self.categories.keys())}")
            return []

        url = f"{self.base_url}{category_path}"
        logger.info(f"Scraping URL: {url}")
        logger.info(f"Looking for selector: {self.parser.selectors['product_container']}")
        products = []

        try:
            with self.session_manager as driver:
                # Navigate to category page
                logger.info("Navigating to page...")
                driver.get(url)
                self._random_delay()
                logger.info("Page loaded, waiting for products...")

                # Wait for products to load
                try:
                    WebDriverWait(driver, self.timeout).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, self.parser.selectors['product_container'])
                        )
                    )
                    logger.info("Products container found!")
                except TimeoutException:
                    logger.error(f"TIMEOUT: Could not find selector '{self.parser.selectors['product_container']}' on {url}")
                    
                    # Debug: Try to find what's actually on the page
                    try:
                        from selenium.webdriver.common.by import By
                        all_links = driver.find_elements(By.TAG_NAME, 'a')
                        logger.error(f"DEBUG: Found {len(all_links)} <a> tags on page")
                        
                        product_cards = driver.find_elements(By.CSS_SELECTOR, '.product-card')
                        logger.error(f"DEBUG: Found {len(product_cards)} elements with class 'product-card'")
                        
                        # Save page source for debugging
                        html = driver.page_source
                        logger.error(f"DEBUG: Page HTML length: {len(html)} characters")
                        logger.error(f"DEBUG: First 500 chars: {html[:500]}")
                        
                        # Check if page is showing cookie consent or other blocking element
                        if 'cookie' in html.lower() or 'samtykke' in html.lower():
                            logger.error("DEBUG: Cookie consent dialog may be blocking content")
                        if 'robot' in html.lower() or 'captcha' in html.lower():
                            logger.error("DEBUG: CAPTCHA or robot detection may be blocking")
                            
                    except Exception as debug_error:
                        logger.error(f"DEBUG error: {debug_error}")
                    
                    return products

                # Scroll to load more products
                logger.info("Scrolling page to load more products...")
                self._scroll_page(driver, max_products)

                # Get page HTML and parse
                logger.info("Getting page HTML...")
                html = driver.page_source
                logger.info(f"HTML length: {len(html)} characters")
                
                logger.info("Parsing products from HTML...")
                products = self.parser.parse_products(html)
                logger.info(f"Parser returned {len(products)} products")

                # Limit to max_products
                products = products[:max_products]

                # Add category to each product
                for product in products:
                    product['category'] = category

                logger.info(f"Successfully scraped {len(products)} products from {category}")

        except Exception as e:
            logger.error(f"Error scraping category {category}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

        return products

    def _scroll_page(self, driver, max_products: int):
        """Scroll page to load more products dynamically"""
        last_height = driver.execute_script("return document.body.scrollHeight")
        products_loaded = 0
        scroll_attempts = 0
        max_scroll_attempts = 10

        while products_loaded < max_products and scroll_attempts < max_scroll_attempts:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Calculate new height
            new_height = driver.execute_script("return document.body.scrollHeight")

            # Check if we've reached the bottom
            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0

            last_height = new_height

            # Count loaded products
            try:
                product_elements = driver.find_elements(
                    By.CSS_SELECTOR,
                    self.parser.selectors['product_container']
                )
                products_loaded = len(product_elements)
                logger.debug(f"Loaded {products_loaded} products after scroll")
            except Exception as e:
                logger.warning(f"Error counting products: {e}")
                break

    def scrape_all_categories(self, max_products_per_category: int = 50) -> Dict[str, List[Dict]]:
        """
        Scrape all available categories
        
        Args:
            max_products_per_category: Maximum products per category
            
        Returns:
            Dictionary mapping category names to product lists
        """
        logger.info("Starting scrape for all categories")
        results = {}

        for category in self.categories.keys():
            logger.info(f"Scraping category: {category}")
            products = self.scrape_category(category, max_products_per_category)
            results[category] = products
            self._random_delay()  # Delay between categories

        total_products = sum(len(products) for products in results.values())
        logger.info(f"Completed scraping all categories: {total_products} total products")

        return results

    def scrape_single_product(self, url: str) -> Optional[Dict]:
        """
        Scrape a single product by URL
        
        Args:
            url: Full product URL
            
        Returns:
            Product dictionary or None
        """
        logger.info(f"Scraping single product: {url}")

        try:
            with self.session_manager as driver:
                driver.get(url)
                self._random_delay()

                # Wait for page load
                try:
                    WebDriverWait(driver, self.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                    )
                except TimeoutException:
                    logger.warning(f"Timeout loading product page: {url}")
                    return None

                html = driver.page_source
                products = self.parser.parse_products(html)

                if products:
                    product = products[0]
                    product['url'] = url
                    logger.info(f"Successfully scraped product: {product.get('name')}")
                    return product

        except Exception as e:
            logger.error(f"Error scraping single product {url}: {e}")

        return None

    def __del__(self):
        """Cleanup on object destruction"""
        if hasattr(self, 'session_manager'):
            self.session_manager.close()

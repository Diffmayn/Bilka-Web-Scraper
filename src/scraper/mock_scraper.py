"""
Mock scraper for testing without actual web scraping
"""

import random
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MockBilkaScraper:
    """Mock scraper that generates fake product data for testing"""

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = config_path
        logger.info("Initialized Mock Scraper (no actual web scraping)")

    def _generate_product(self, index: int, category: str) -> Dict:
        """Generate a single mock product"""
        product_names = {
            'electronics': [
                'Samsung Galaxy Phone', 'Apple iPhone', 'Sony Headphones',
                'LG Smart TV', 'Dell Laptop', 'HP Printer', 'Logitech Mouse',
                'Samsung Tablet', 'Canon Camera', 'Nintendo Switch'
            ],
            'home': [
                'Kitchen Mixer', 'Coffee Maker', 'Vacuum Cleaner',
                'Microwave Oven', 'Air Fryer', 'Blender', 'Toaster',
                'Electric Kettle', 'Food Processor', 'Rice Cooker'
            ],
            'fashion': [
                'Designer Jacket', 'Running Shoes', 'Winter Coat',
                'Leather Boots', 'Dress Shirt', 'Jeans', 'Sneakers',
                'Summer Dress', 'Polo Shirt', 'Sports Watch'
            ],
            'sports': [
                'Yoga Mat', 'Dumbbell Set', 'Exercise Bike',
                'Treadmill', 'Resistance Bands', 'Protein Powder',
                'Running Shoes', 'Bicycle', 'Tennis Racket', 'Golf Clubs'
            ]
        }

        names = product_names.get(category, product_names['electronics'])
        name = f"{random.choice(names)} - Model {random.randint(100, 999)}"

        # Generate prices
        regular_price = round(random.uniform(100, 5000), 2)

        # Some products have discounts, some don't
        has_discount = random.random() < 0.6  # 60% chance of discount

        if has_discount:
            # Most discounts are reasonable (5-50%), some are extreme (50-95%)
            if random.random() < 0.95:  # 95% are normal discounts
                discount_percentage = round(random.uniform(5, 50), 1)
            else:  # 5% are suspiciously high discounts
                discount_percentage = round(random.uniform(60, 95), 1)

            sale_price = round(regular_price * (1 - discount_percentage / 100), 2)
            current_price = sale_price
            original_price = regular_price
        else:
            discount_percentage = 0
            current_price = regular_price
            original_price = None

        return {
            'name': name,
            'current_price': current_price,
            'original_price': original_price,
            'discount_percentage': discount_percentage,
            'category': category,
            'url': f'https://bilka.dk/product/{category}/{index}',
            'image_url': f'https://bilka.dk/images/{category}/{index}.jpg',
            'brand': random.choice(['Samsung', 'Sony', 'LG', 'Apple', 'HP', 'Dell']),
            'availability': random.choice(['In Stock', 'Low Stock', 'Out of Stock']),
            'scraped_at': datetime.now()
        }

    def scrape_category(self, category: str, max_products: int = 100) -> List[Dict]:
        """Generate mock products for a category"""
        logger.info(f"Mock scraping {max_products} products from category: {category}")

        # Simulate scraping delay
        time.sleep(random.uniform(0.5, 1.5))

        products = [
            self._generate_product(i, category)
            for i in range(max_products)
        ]

        logger.info(f"Generated {len(products)} mock products")
        return products

    def scrape_all_categories(self, max_products_per_category: int = 50) -> Dict[str, List[Dict]]:
        """Generate mock products for all categories"""
        logger.info("Mock scraping all categories")

        categories = ['electronics', 'home', 'fashion', 'sports']
        results = {}

        for category in categories:
            products = self.scrape_category(category, max_products_per_category)
            results[category] = products
            time.sleep(0.5)  # Simulate delay between categories

        total_products = sum(len(products) for products in results.values())
        logger.info(f"Generated {total_products} total mock products")

        return results

    def scrape_single_product(self, url: str) -> Optional[Dict]:
        """Generate a single mock product"""
        logger.info(f"Mock scraping single product: {url}")
        time.sleep(random.uniform(0.3, 0.8))

        # Extract category from URL if possible
        category = 'electronics'
        for cat in ['electronics', 'home', 'fashion', 'sports']:
            if cat in url:
                category = cat
                break

        return self._generate_product(0, category)

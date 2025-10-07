"""Quick scraper test without emojis"""
import sys
sys.path.insert(0, '.')

from src.scraper.bilka_scraper import BilkaScraper

print("Testing scraper...")
scraper = BilkaScraper()
products = scraper.scrape_category('electronics', max_products=3)

print(f"\nFound {len(products)} products:\n")
for i, p in enumerate(products[:5], 1):
    print(f"{i}. {p['name'][:60]}")
    print(f"   Current: {p.get('current_price')} kr")
    print(f"   Original: {p.get('original_price')} kr")
    print(f"   Discount: {p.get('discount_percentage')}%")
    print()

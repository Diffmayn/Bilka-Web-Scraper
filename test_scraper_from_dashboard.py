"""
Test scraper from Streamlit context
This mimics what the dashboard does
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Testing Scraper in Streamlit Context")
print("=" * 60)

# Test 1: Import the scraper
print("\n1. Importing BilkaScraper...")
try:
    from src.scraper.bilka_scraper import BilkaScraper
    print("   ✓ Import successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Create scraper instance
print("\n2. Creating scraper instance...")
try:
    scraper = BilkaScraper()
    print("   ✓ Scraper created")
    print(f"   Base URL: {scraper.base_url}")
    print(f"   Categories: {list(scraper.categories.keys())}")
    print(f"   Headless: {scraper.session_manager.headless}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Try to scrape
print("\n3. Attempting to scrape electronics category...")
try:
    products = scraper.scrape_category('electronics', max_products=10)
    print(f"   ✓ Scrape completed")
    print(f"   Products found: {len(products)}")
    
    if products:
        print("\n   First product:")
        p = products[0]
        print(f"   - Name: {p.get('name', 'N/A')}")
        print(f"   - Current: {p.get('current_price', 'N/A')} kr")
        print(f"   - Original: {p.get('original_price', 'N/A')} kr")
        print(f"   - Discount: {p.get('discount_percent', 'N/A')}%")
    else:
        print("   ⚠️ No products returned!")
        print("\n   This indicates:")
        print("   - ChromeDriver may not be starting")
        print("   - Page load timeout")
        print("   - Bot detection blocking")
        print("   - CSS selectors not matching")
        
except Exception as e:
    print(f"   ❌ Scrape failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
if products:
    print("✅ TEST PASSED - Scraper working!")
else:
    print("❌ TEST FAILED - No products found")
print("=" * 60)

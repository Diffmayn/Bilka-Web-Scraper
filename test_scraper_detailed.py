"""
Quick test script to diagnose scraping issues
Shows detailed logs to help identify problems
"""

import logging
import sys
import os

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/test_scraper.log')
    ]
)

logger = logging.getLogger(__name__)

def test_scraper():
    """Test the scraper with detailed logging"""
    
    print("\n" + "="*80)
    print("BILKA SCRAPER DIAGNOSTIC TEST")
    print("="*80 + "\n")
    
    # Test 1: Check configuration files
    print("📋 TEST 1: Checking configuration files...")
    try:
        import yaml
        
        # Check settings.yaml
        with open('config/settings.yaml', 'r') as f:
            settings = yaml.safe_load(f)
            print(f"✅ settings.yaml loaded")
            print(f"   Base URL: {settings.get('bilka', {}).get('base_url')}")
            print(f"   Categories: {list(settings.get('bilka', {}).get('categories', {}).keys())}")
        
        # Check scraping_rules.yaml
        with open('config/scraping_rules.yaml', 'r') as f:
            rules = yaml.safe_load(f)
            print(f"✅ scraping_rules.yaml loaded")
            print(f"   Product container: {rules.get('selectors', {}).get('product_container')}")
            print(f"   Product name: {rules.get('selectors', {}).get('product_name')}")
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    print()
    
    # Test 2: Check ChromeDriver availability
    print("🔧 TEST 2: Checking ChromeDriver...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        print("   Attempting to start ChromeDriver...")
        
        # Try with system chromium first (for Linux/Streamlit Cloud)
        import platform
        if platform.system() == 'Linux':
            print("   Detected Linux - trying Chromium...")
            chrome_options.binary_location = '/usr/bin/chromium'
        
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ ChromeDriver started successfully")
        driver.quit()
        
    except Exception as e:
        print(f"❌ ChromeDriver error: {e}")
        print("   This is likely why scraping fails on Streamlit Cloud")
        print("   Recommendation: Check packages.txt and Streamlit Cloud logs")
        return False
    
    print()
    
    # Test 3: Try to scrape products
    print("🌐 TEST 3: Testing real scrape...")
    try:
        from src.scraper.bilka_scraper import BilkaScraper
        
        scraper = BilkaScraper()
        print(f"✅ Scraper initialized")
        print(f"   Base URL: {scraper.base_url}")
        print(f"   Selector: {scraper.parser.selectors['product_container']}")
        
        # Try to scrape 5 products
        print("\n   Attempting to scrape 5 products from electronics...")
        print("   (This may take 10-20 seconds...)")
        products = scraper.scrape_category('electronics', max_products=5)
        
        if products:
            print(f"✅ Found {len(products)} products!")
            print("\n   Sample products:")
            for i, product in enumerate(products[:3], 1):
                print(f"   {i}. {product.get('name', 'NO NAME')[:60]}")
                print(f"      Price: {product.get('current_price')} kr")
                print(f"      Discount: {product.get('discount_percentage', 0)}%")
        else:
            print(f"❌ No products found")
            print("   Check logs/test_scraper.log for detailed error messages")
            return False
            
    except Exception as e:
        print(f"❌ Scraping error: {e}")
        import traceback
        print("\n   Full traceback:")
        print(traceback.format_exc())
        return False
    
    print()
    print("="*80)
    print("✅ ALL TESTS PASSED!")
    print("="*80)
    return True

if __name__ == "__main__":
    # Make sure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Run tests
    success = test_scraper()
    
    if not success:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("📄 Detailed logs saved to: logs/test_scraper.log")
        sys.exit(1)
    else:
        print("\n✅ Scraper is working correctly!")
        sys.exit(0)

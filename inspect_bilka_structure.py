"""
Test script to inspect actual Bilka.dk HTML structure
Run this locally to find the correct CSS selectors
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup

def inspect_bilka_page():
    """Inspect Bilka.dk product page structure"""
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Add user agent
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Use existing ChromeDriver from drivers folder
    try:
        driver = webdriver.Chrome(
            service=Service("drivers/chromedriver.exe"),
            options=chrome_options
        )
    except Exception as e:
        print(f"❌ Error starting ChromeDriver: {e}")
        print("Trying without specifying driver path...")
        driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to Bilka laptops page
        url = "https://www.bilka.dk/elektronik/computere-og-gaming/computere/type/baerbar-computer/windows-computer/pl/windows-baerbar/"
        print(f"\n🔍 Inspecting: {url}\n")
        
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Get page source
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        print("=" * 80)
        print("ANALYZING PAGE STRUCTURE")
        print("=" * 80)
        
        # Look for common product container patterns
        print("\n📦 Looking for product containers...\n")
        
        potential_containers = [
            'article', 'div[data-product]', 'div[data-id]', '.product', '.item',
            '[class*="product"]', '[class*="card"]', '[class*="item"]',
            '[data-testid*="product"]', '[class*="tile"]', '[class*="grid-item"]'
        ]
        
        found_containers = []
        for selector in potential_containers:
            elements = soup.select(selector)
            if len(elements) > 5:  # Likely a product list if > 5 elements
                found_containers.append((selector, len(elements)))
                print(f"✓ Found {len(elements)} elements with selector: {selector}")
        
        if not found_containers:
            print("❌ No obvious product containers found!")
            print("\nLet's look at all elements with class containing 'product':")
            all_with_product = soup.find_all(class_=lambda x: x and 'product' in x.lower())
            for elem in all_with_product[:5]:
                print(f"  - {elem.name} class='{elem.get('class')}'")
        
        # Analyze the first potential container in detail
        if found_containers:
            print("\n" + "=" * 80)
            print("DETAILED ANALYSIS OF FIRST PRODUCT CONTAINER")
            print("=" * 80)
            
            best_selector, count = found_containers[0]
            first_product = soup.select(best_selector)[0]
            
            print(f"\n📋 Using selector: {best_selector}")
            print(f"Found {count} products\n")
            
            # Look for product name
            print("🏷️  Product Name - checking:")
            for name_sel in ['h1', 'h2', 'h3', 'h4', '[class*="title"]', '[class*="name"]', 'a[href*="/p/"]']:
                elem = first_product.select_one(name_sel)
                if elem:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 5:
                        print(f"   ✓ {name_sel}: '{text[:60]}...'")
            
            # Look for prices
            print("\n💰 Prices - checking:")
            for price_sel in ['[class*="price"]', '[class*="amount"]', '[data-price]', 'span', 'div']:
                elems = first_product.select(price_sel)
                for elem in elems:
                    text = elem.get_text(strip=True)
                    if any(char.isdigit() for char in text) and ('kr' in text.lower() or ',' in text):
                        print(f"   ✓ {price_sel}: '{text}'")
                        break
            
            # Look for discount
            print("\n🏷️  Discount - checking:")
            for disc_sel in ['[class*="discount"]', '[class*="save"]', '[class*="badge"]', '[class*="percent"]']:
                elem = first_product.select_one(disc_sel)
                if elem:
                    text = elem.get_text(strip=True)
                    if '%' in text or 'spar' in text.lower():
                        print(f"   ✓ {disc_sel}: '{text}'")
            
            # Look for images
            print("\n🖼️  Image - checking:")
            imgs = first_product.select('img')
            for img in imgs:
                src = img.get('src', img.get('data-src', ''))
                if src and 'product' in src.lower() or 'bilka' in src.lower():
                    print(f"   ✓ img src: '{src[:80]}...'")
                    break
            
            # Look for URLs
            print("\n🔗 Product URL - checking:")
            links = first_product.select('a[href]')
            for link in links:
                href = link.get('href', '')
                if '/p/' in href or '/produkt' in href:
                    print(f"   ✓ a[href]: '{href[:80]}...'")
                    break
            
            # Print full HTML of first product (truncated)
            print("\n" + "=" * 80)
            print("FIRST PRODUCT HTML (first 2000 chars):")
            print("=" * 80)
            print(str(first_product)[:2000])
            print("...")
        
        # Save full HTML for inspection
        with open('data/bilka_page_dump.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("\n✅ Full HTML saved to: data/bilka_page_dump.html")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        if found_containers:
            print(f"\n✓ Use this as product_container: '{found_containers[0][0]}'")
            print("\nUpdate config/scraping_rules.yaml with the selectors printed above.")
        else:
            print("\n⚠️  Could not find product containers automatically.")
            print("Please inspect data/bilka_page_dump.html manually to find the correct selectors.")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    inspect_bilka_page()

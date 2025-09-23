"""
Simple Chrome test script to verify ChromeDriver functionality
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os
import sys

def test_chrome():
    """Test Chrome WebDriver functionality."""
    print("Testing Chrome WebDriver...")

    # Set up Chrome options
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--headless")  # Try with headless first

    try:
        # Try with webdriver-manager
        from webdriver_manager.chrome import ChromeDriverManager
        print("Using webdriver-manager...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        print("✅ Chrome started successfully!")
        driver.get("https://www.google.com")
        print(f"Page title: {driver.title}")
        driver.quit()
        return True

    except Exception as e:
        print(f"❌ Error with webdriver-manager: {e}")

        try:
            # Try without webdriver-manager
            print("Trying without webdriver-manager...")
            driver = webdriver.Chrome(options=options)
            print("✅ Chrome started successfully!")
            driver.get("https://www.google.com")
            print(f"Page title: {driver.title}")
            driver.quit()
            return True

        except Exception as e2:
            print(f"❌ Error without webdriver-manager: {e2}")
            return False

if __name__ == "__main__":
    success = test_chrome()
    if success:
        print("🎉 Chrome WebDriver test passed!")
        sys.exit(0)
    else:
        print("💥 Chrome WebDriver test failed!")
        sys.exit(1)
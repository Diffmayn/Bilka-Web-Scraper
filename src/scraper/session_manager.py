"""
Session Manager for handling Selenium WebDriver instances
Includes anti-detection measures and session management
"""

import random
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages Chrome WebDriver sessions with stealth capabilities"""

    def __init__(self, headless: bool = True, user_agent: Optional[str] = None):
        self.headless = headless
        self.user_agent = user_agent or self._get_random_user_agent()
        self.driver: Optional[webdriver.Chrome] = None

    def _get_random_user_agent(self) -> str:
        """Get a random user agent string"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        return random.choice(user_agents)

    def _create_chrome_options(self) -> Options:
        """Create Chrome options with anti-detection measures"""
        options = Options()

        # Basic options
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"user-agent={self.user_agent}")

        # Anti-detection measures
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Performance optimizations
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        
        # Privacy settings
        options.add_argument("--incognito")
        
        # Additional options for Streamlit Cloud / Linux
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--remote-debugging-port=9222")

        return options

    def create_driver(self) -> webdriver.Chrome:
        """Create and return a new Chrome WebDriver instance"""
        try:
            options = self._create_chrome_options()

            # Try with webdriver-manager first
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from webdriver_manager.core.os_manager import ChromeType
                
                # Check if running on Linux (Streamlit Cloud)
                import platform
                if platform.system() == 'Linux':
                    # Use chromium on Linux
                    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
                else:
                    # Use regular Chrome on Windows/Mac
                    service = Service(ChromeDriverManager().install())
                    
                driver = webdriver.Chrome(service=service, options=options)
                logger.info("Chrome WebDriver created with webdriver-manager")
            except Exception as e:
                logger.warning(f"webdriver-manager failed: {e}, trying default ChromeDriver")
                # Fall back to default ChromeDriver
                driver = webdriver.Chrome(options=options)
                logger.info("Chrome WebDriver created with system ChromeDriver")

            # Additional stealth JavaScript
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """
            })

            self.driver = driver
            logger.info("Chrome WebDriver initialized successfully")
            return driver

        except WebDriverException as e:
            logger.error(f"Failed to create Chrome WebDriver: {e}")
            raise

    def get_driver(self) -> webdriver.Chrome:
        """Get the current driver or create a new one"""
        if self.driver is None:
            return self.create_driver()
        return self.driver

    def close(self):
        """Close the current driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome WebDriver closed")
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            finally:
                self.driver = None

    def random_delay(self, min_seconds: float = 2, max_seconds: float = 5):
        """Add a random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def __enter__(self):
        """Context manager entry"""
        return self.get_driver()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

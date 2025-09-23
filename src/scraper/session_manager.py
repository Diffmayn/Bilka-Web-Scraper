"""
Session Manager for Bilka Price Monitor

Handles Chrome WebDriver initialization, user-agent rotation,
cookie management, and session persistence for web scraping.
"""

import random
import time
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import yaml
import os
from loguru import logger


class ScrapingError(Exception):
    """Base exception for scraping operations."""
    pass


class SessionManager:
    """
    Manages browser sessions for web scraping with stealth capabilities.

    Features:
    - Chrome WebDriver with anti-detection measures
    - User-agent rotation
    - Random delays between requests
    - Cookie persistence
    - Proxy support
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        Initialize the session manager.

        Args:
            config_path: Path to the configuration YAML file
        """
        self.config = self._load_config(config_path)
        self.driver: Optional[webdriver.Chrome] = None
        self.user_agents = self.config['scraping']['user_agents']
        self.current_user_agent = None
        self.cookies_file = "data/cookies.pkl"

        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        logger.info("Session Manager initialized")

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
            'scraping': {
                'user_agents': [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                ],
                'request_delay_min': 2,
                'request_delay_max': 5,
                'timeout': 30,
                'headless': True
            }
        }

    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the configured list."""
        return random.choice(self.user_agents)

    def _setup_chrome_options(self) -> Options:
        """
        Configure Chrome options for stealth scraping.

        Returns:
            Configured Chrome Options object
        """
        options = Options()

        # Basic stealth options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Windows-specific options to avoid permission issues
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")

        # User agent
        self.current_user_agent = self._get_random_user_agent()
        options.add_argument(f"--user-agent={self.current_user_agent}")

        # Window size and other options
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Speed up loading

        # Headless mode
        if self.config['scraping'].get('headless', True):
            options.add_argument("--headless")

        # SSL and certificate options for handling certificate issues
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--ignore-certificate-errors-spki-list")
        options.add_argument("--ignore-ssl-errors-ignore-untrusted")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-web-security")

        return options

    def start_session(self) -> webdriver.Chrome:
        """
        Start a new browser session.

        Returns:
            Configured Chrome WebDriver instance

        Raises:
            ScrapingError: If session cannot be started
        """
        try:
            logger.info("Starting new browser session...")

            options = self._setup_chrome_options()

            # Use Selenium Manager to automatically manage ChromeDriver
            try:
                # Try to use manually downloaded ChromeDriver first
                chromedriver_path = os.path.join(os.path.dirname(__file__), "..", "..", "drivers", "chromedriver.exe")
                if os.path.exists(chromedriver_path):
                    service = Service(executable_path=chromedriver_path)
                    logger.info(f"Using manually downloaded ChromeDriver: {chromedriver_path}")
                else:
                    # Try Selenium Manager (available in Selenium 4.11+)
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    logger.info("Using Selenium Manager for ChromeDriver")
            except ImportError:
                # Fallback to automatic management
                service = Service()
                logger.info("Using automatically managed ChromeDriver")

            self.driver = webdriver.Chrome(service=service, options=options)

            # Execute JavaScript to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Load cookies if they exist
            self._load_cookies()

            logger.info(f"Browser session started with user agent: {self.current_user_agent}")
            return self.driver

        except WebDriverException as e:
            error_msg = f"Failed to start browser session: {e}"
            logger.error(error_msg)
            raise ScrapingError(error_msg)

    def end_session(self) -> None:
        """End the current browser session."""
        if self.driver:
            try:
                # Save cookies before closing
                self._save_cookies()

                self.driver.quit()
                self.driver = None
                logger.info("Browser session ended")
            except Exception as e:
                logger.warning(f"Error ending session: {e}")

    def navigate_to_url(self, url: str, wait_for_element: Optional[str] = None) -> bool:
        """
        Navigate to a URL with error handling and optional element waiting.

        Args:
            url: The URL to navigate to
            wait_for_element: CSS selector to wait for (optional)

        Returns:
            True if navigation successful, False otherwise
        """
        if not self.driver:
            logger.error("No active session. Call start_session() first.")
            return False

        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)

            # Random delay to appear more human-like
            delay = random.uniform(
                self.config['scraping']['request_delay_min'],
                self.config['scraping']['request_delay_max']
            )
            time.sleep(delay)

            # Wait for element if specified
            if wait_for_element:
                WebDriverWait(self.driver, self.config['scraping']['timeout']).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                )

            return True

        except TimeoutException:
            logger.warning(f"Timeout waiting for element: {wait_for_element}")
            return False
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return False

    def _load_cookies(self) -> None:
        """Load cookies from file if exists."""
        try:
            import pickle
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                    for cookie in cookies:
                        try:
                            self.driver.add_cookie(cookie)
                        except Exception as e:
                            logger.debug(f"Could not add cookie: {e}")
                logger.info("Cookies loaded successfully")
        except Exception as e:
            logger.debug(f"Could not load cookies: {e}")

    def _save_cookies(self) -> None:
        """Save current cookies to file."""
        try:
            import pickle
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            logger.debug("Cookies saved successfully")
        except Exception as e:
            logger.debug(f"Could not save cookies: {e}")

    def get_page_source(self) -> str:
        """
        Get the current page source.

        Returns:
            HTML source of the current page
        """
        if not self.driver:
            return ""
        return self.driver.page_source

    def wait_for_element(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        Wait for an element to be present on the page.

        Args:
            selector: CSS selector to wait for
            timeout: Timeout in seconds (uses config default if None)

        Returns:
            True if element found, False otherwise
        """
        if not self.driver:
            return False

        timeout = timeout or self.config['scraping']['timeout']

        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return True
        except TimeoutException:
            logger.debug(f"Element not found: {selector}")
            return False

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the page to load dynamic content."""
        if self.driver:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # Wait for content to load

    def __enter__(self):
        """Context manager entry."""
        self.start_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.end_session()


# Convenience function for quick scraping sessions
def create_session(config_path: str = "config/settings.yaml") -> SessionManager:
    """
    Create and return a new session manager instance.

    Args:
        config_path: Path to configuration file

    Returns:
        Configured SessionManager instance
    """
    return SessionManager(config_path)
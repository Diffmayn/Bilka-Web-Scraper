#!/usr/bin/env python3
"""
Setup script for Bilka Price Monitor

This script helps set up the development environment and installs dependencies.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("Please use Python 3.11 or higher")
        return False


def install_dependencies():
    """Install Python dependencies."""
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False

    return run_command("pip install -r requirements.txt", "Installing dependencies")


def setup_virtual_environment():
    """Set up Python virtual environment."""
    if Path("venv").exists():
        print("ℹ️  Virtual environment already exists")
        return True

    # Create virtual environment
    if not run_command("python -m venv venv", "Creating virtual environment"):
        return False

    # Activate and upgrade pip
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
    else:  # Unix/Linux
        activate_cmd = "source venv/bin/activate"

    return run_command(f"{activate_cmd} && python -m pip install --upgrade pip",
                      "Upgrading pip in virtual environment")


def initialize_database():
    """Initialize the database."""
    return run_command("python main.py init", "Initializing database")


def create_directories():
    """Create necessary directories."""
    directories = ["data/raw", "data/processed", "data/exports", "logs"]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

    return True


def check_chrome_driver():
    """Check if Chrome WebDriver is available."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service

        # Try to create a WebDriver instance
        service = Service()
        driver = webdriver.Chrome(service=service)
        driver.quit()
        print("✅ Chrome WebDriver is working")
        return True
    except Exception as e:
        print(f"⚠️  Chrome WebDriver check failed: {e}")
        print("Please download Chrome WebDriver from: https://chromedriver.chromium.org/")
        return False


def main():
    """Main setup function."""
    print("🚀 Bilka Price Monitor Setup")
    print("=" * 50)

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    success_count = 0
    total_steps = 6

    # Step 1: Check Python version
    if check_python_version():
        success_count += 1

    # Step 2: Create directories
    if create_directories():
        success_count += 1

    # Step 3: Setup virtual environment
    if setup_virtual_environment():
        success_count += 1

    # Step 4: Install dependencies
    if install_dependencies():
        success_count += 1

    # Step 5: Initialize database
    if initialize_database():
        success_count += 1

    # Step 6: Check Chrome WebDriver
    if check_chrome_driver():
        success_count += 1

    print("\n" + "=" * 50)
    print(f"Setup completed: {success_count}/{total_steps} steps successful")

    if success_count == total_steps:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Activate virtual environment: source venv/bin/activate")
        print("2. Start dashboard: python main.py dashboard")
        print("3. Or run scraping: python main.py scrape --category electronics")
    else:
        print("⚠️  Setup completed with some issues")
        print("Please check the error messages above and try again")

    return success_count == total_steps


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
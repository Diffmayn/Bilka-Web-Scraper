#!/usr/bin/env python3
"""
Bilka Price Monitor - POC Test
Tests the simple web-based POC functionality
"""

import os
import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Add project path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_database_setup():
    """Test database creation and basic functionality"""
    print("🔍 Testing database setup...")

    # Check if simple_poc.py exists
    assert os.path.exists("simple_poc.py"), "simple_poc.py not found"

    # Import the POC module to test database setup
    try:
        from simple_poc import SimpleBilkaMonitor
        monitor = SimpleBilkaMonitor()

        # Check if database was created
        assert os.path.exists("data/bilka_poc.db"), "Database file data/bilka_poc.db not created"
        print("✅ Database created successfully")

        # Test basic database operations
        conn = sqlite3.connect("data/bilka_poc.db")
        cursor = conn.cursor()

        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]

        assert 'products' in table_names and 'scrape_log' in table_names, "Database tables missing"
        print("✅ Database tables created correctly")
        conn.close()
        return

    except ImportError as e:
        raise
    except Exception as e:
        raise

def test_dependencies():
    """Test if required dependencies are available"""
    print("🔍 Testing dependencies...")

    required_modules = ['streamlit', 'pandas', 'sqlite3', 'requests', 'bs4']

    missing_modules = []
    for module in required_modules:
        try:
            if module == 'sqlite3':
                import sqlite3
            elif module == 'bs4':
                import bs4
            else:
                __import__(module)
            print(f"✅ {module} available")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module} missing")

    assert len(missing_modules) == 0, f"Missing modules: {missing_modules}"

def test_file_structure():
    """Test if all required files exist"""
    print("🔍 Testing file structure...")

    required_files = [
        'simple_poc.py',
        'run_poc.bat',
        'setup_poc.bat',
        'requirements_poc.txt'
    ]

    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path} missing")

    assert len(missing_files) == 0, f"Missing files: {missing_files}"

def main():
    print("🧪 Bilka Price Monitor - POC Test Suite")
    print("=" * 45)

    tests_passed = 0
    total_tests = 3

    # Test 1: File structure
    if test_file_structure():
        tests_passed += 1
    print()

    # Test 2: Dependencies
    if test_dependencies():
        tests_passed += 1
    print()

    # Test 3: Database setup
    if test_database_setup():
        tests_passed += 1
    print()

    # Results
    print("=" * 45)
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("\n🚀 Your POC is ready to run!")
        print("\n📋 Next steps:")
        print("1. Run: setup_poc.bat (if not done already)")
        print("2. Run: run_poc.bat")
        print("3. Open: http://localhost:8501")
        print("\n✨ Features ready:")
        print("   • Web-based dashboard")
        print("   • Real BILKA.dk scraping")
        print("   • SQLite database (~2000 record limit)")
        print("   • No external applications needed")
        return True
    else:
        print(f"❌ {total_tests - tests_passed} test(s) failed")
        print("\n🔧 To fix:")
        print("1. Run: pip install -r requirements_poc.txt")
        print("2. Make sure all files are present")
        print("3. Run this test again")
        return False

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
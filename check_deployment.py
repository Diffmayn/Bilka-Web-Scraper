#!/usr/bin/env python3
"""
Bilka Price Monitor - Deployment Readiness Check
Checks if your project is ready for Docker-free deployment
"""

import sys
import os

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print("   ✅ Python 3.10+ installed")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} found. Need 3.10+")
        return False

def check_pip_packages():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'pandas',
        'plotly',
        'sqlalchemy'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package} installed")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package} missing")

    return len(missing_packages) == 0

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        'streamlit_app.py',
        'src/ui/dashboard.py',
        'requirements_cloud.txt',
        'main.py'
    ]

    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path} exists")
        else:
            missing_files.append(file_path)
            print(f"   ❌ {file_path} missing")

    return len(missing_files) == 0

def check_database():
    """Check if database is initialized"""
    db_paths = [
        'data/bilka_prices.db',
        'data/bilka_prices.sqlite',
        'bilka_prices.db'
    ]

    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"   ✅ Database found: {db_path}")
            return True

    print("   ⚠️  No database found (will be created on first run)")
    return True  # Not a blocking issue

def main():
    print("🔍 Bilka Price Monitor - Deployment Readiness Check")
    print("=" * 55)
    print("Checking if your project is ready for online deployment...\n")

    all_checks_passed = True

    # Check 1: Python version
    print("1. Checking Python version...")
    if not check_python_version():
        all_checks_passed = False
    print()

    # Check 2: Required packages
    print("2. Checking required packages...")
    if not check_pip_packages():
        all_checks_passed = False
    print()

    # Check 3: Required files
    print("3. Checking required files...")
    if not check_required_files():
        all_checks_passed = False
    print()

    # Check 4: Database
    print("4. Checking database...")
    if not check_database():
        all_checks_passed = False
    print()

    # Summary and next steps
    print("=" * 55)
    if all_checks_passed:
        print("🎉 READY FOR DEPLOYMENT!")
        print("\n🚀 Choose your deployment method:")
        print("\n📋 Option A: Streamlit Cloud (Recommended)")
        print("   1. Commit your code to GitHub")
        print("   2. Go to: https://share.streamlit.io")
        print("   3. Connect your GitHub repo")
        print("   4. Select 'streamlit_app.py' as main file")
        print("   5. Click Deploy!")
        print("\n📋 Option B: Local + Ngrok")
        print("   1. Run: go_online_local.bat")
        print("   2. Download ngrok from: https://ngrok.com/download")
        print("   3. Run: ngrok http 8501")
        print("   4. Share the HTTPS URL!")
        print("\n📖 For detailed instructions, see: DOCKER_FREE_DEPLOYMENT.md")

    else:
        print("❌ SOME CHECKS FAILED!")
        print("\n🔧 To fix the issues:")
        print("   1. Install missing Python packages: pip install -r requirements_cloud.txt")
        print("   2. Make sure all files are present")
        print("   3. Run this check again: python check_deployment.py")
        print("\n📖 See DOCKER_FREE_DEPLOYMENT.md for help")

    return all_checks_passed

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
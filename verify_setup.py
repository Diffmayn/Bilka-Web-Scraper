"""
Quick verification that everything is set up correctly
"""
import sys

print("=" * 60)
print("  Bilka Price Monitor - Setup Verification")
print("=" * 60)
print()

# Test 1: Python version
print("1. Python Version:", sys.version.split()[0])
if sys.version_info < (3, 10):
    print("   ❌ Python 3.10 or higher required!")
    sys.exit(1)
else:
    print("   ✓ OK")
print()

# Test 2: Required imports
print("2. Testing dependencies...")
required = {
    'streamlit': 'Streamlit',
    'sqlalchemy': 'SQLAlchemy',
    'selenium': 'Selenium',
    'bs4': 'BeautifulSoup4',
    'yaml': 'PyYAML',
    'pandas': 'Pandas',
    'numpy': 'NumPy',
    'sklearn': 'scikit-learn'
}

missing = []
for module, name in required.items():
    try:
        __import__(module)
        print(f"   ✓ {name}")
    except ImportError:
        print(f"   ❌ {name} - NOT INSTALLED")
        missing.append(name)

if missing:
    print()
    print(f"Missing packages: {', '.join(missing)}")
    print()
    print("Install with:")
    print("python -m pip install " + " ".join([m.lower().replace('-', '_') for m in missing]))
    sys.exit(1)

print()

# Test 3: Dashboard import
print("3. Testing dashboard import...")
try:
    from src.ui.dashboard import main
    print("   ✓ Dashboard imports successfully")
except Exception as e:
    print(f"   ❌ Dashboard import failed: {e}")
    sys.exit(1)

print()

# Test 4: Config files
print("4. Checking configuration files...")
import os
config_files = [
    'config/settings.yaml',
    'config/scraping_rules.yaml',
    'streamlit_app.py'
]

for file in config_files:
    if os.path.exists(file):
        print(f"   ✓ {file}")
    else:
        print(f"   ❌ {file} - NOT FOUND")

print()

# Test 5: ChromeDriver
print("5. Checking ChromeDriver...")
chromedriver_paths = [
    'drivers/chromedriver.exe',
    'drivers/chromedriver-win64/chromedriver.exe'
]

found = False
for path in chromedriver_paths:
    if os.path.exists(path):
        print(f"   ✓ Found: {path}")
        found = True
        break

if not found:
    print("   ⚠️ ChromeDriver not found in drivers/ folder")
    print("   (Will attempt to download automatically)")

print()

# Final status
print("=" * 60)
print("  ✅ SETUP VERIFICATION COMPLETE!")
print("=" * 60)
print()
print("Ready to start! Run:")
print("  • Windows: run_local_dashboard.bat")
print("  • Manual:  python -m streamlit run streamlit_app.py")
print()
print("Dashboard will be available at: http://localhost:8501")
print()

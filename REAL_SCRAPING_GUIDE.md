# 🚀 Real Web Scraping Setup Guide

This guide explains how to run the **real web scraper** (not mock data) for the Bilka Price Monitor.

---

## 🎯 Overview

The application can run in two modes:

1. **Real Scraping Mode** (default) - Scrapes actual data from Bilka.dk
2. **Mock Mode** - Generates test data (set `USE_MOCK_SCRAPER=true`)

---

## 💻 Local Setup (Windows/Mac/Linux)

### Prerequisites

- Python 3.11+
- Chrome browser installed
- Internet connection

### Step 1: Clone and Install

```bash
git clone https://github.com/Diffmayn/Bilka-Web-Scraper.git
cd Bilka-Web-Scraper
pip install -r requirements.txt
```

### Step 2: Initialize Database

```bash
python main.py init
```

### Step 3: Run Real Scraping

```bash
# Make sure USE_MOCK_SCRAPER is NOT set (or set to false)
python main.py scrape --category electronics --max-products 50
```

The scraper will:
- ✅ Automatically download ChromeDriver (via webdriver-manager)
- ✅ Launch Chrome in headless mode
- ✅ Scrape real products from Bilka.dk
- ✅ Store data in SQLite database

### Step 4: Launch Dashboard

```bash
streamlit run streamlit_app.py
```

Open browser to: `http://localhost:8501`

---

## ☁️ Streamlit Cloud Setup

### Option 1: Using Chromium (Recommended)

Streamlit Cloud can run real web scraping with Chromium.

**Setup:**

1. **Create `packages.txt` in your repo root:**
```txt
chromium
chromium-driver
```

2. **Your `requirements.txt` already includes:**
```txt
selenium>=4.15.0
webdriver-manager>=4.0.0
```

3. **Deploy to Streamlit Cloud**
   - The app will automatically use Chromium
   - Real scraping will work!

### Option 2: Fallback to Mock Data

If ChromeDriver setup fails on Streamlit Cloud, the app will automatically:
- ⚠️ Show a warning message
- 🔄 Fall back to mock data generator
- ✅ Continue working normally

---

## 🔧 Configuration

### Force Mock Mode (for testing)

**Windows PowerShell:**
```powershell
$env:USE_MOCK_SCRAPER='true'
python main.py scrape --category electronics --max-products 50
```

**Linux/Mac:**
```bash
export USE_MOCK_SCRAPER=true
python main.py scrape --category electronics --max-products 50
```

**In Code:**
```python
import os
os.environ['USE_MOCK_SCRAPER'] = 'true'
```

### Force Real Scraping

**Windows PowerShell:**
```powershell
$env:USE_MOCK_SCRAPER='false'
# Or remove the variable
Remove-Item Env:\USE_MOCK_SCRAPER
python main.py scrape --category electronics --max-products 50
```

**Linux/Mac:**
```bash
export USE_MOCK_SCRAPER=false
# Or unset it
unset USE_MOCK_SCRAPER
python main.py scrape --category electronics --max-products 50
```

---

## 🌐 How Real Scraping Works

### 1. **ChromeDriver Setup**
- Uses `webdriver-manager` to auto-download correct ChromeDriver version
- Detects your Chrome/Chromium version
- Handles updates automatically

### 2. **Stealth Mode**
The scraper includes anti-detection features:
- Random user agents
- Random delays between requests (2-5 seconds)
- Disabled automation flags
- Incognito mode
- JavaScript modifications to hide WebDriver

### 3. **Data Collection**
```python
# The scraper:
1. Navigates to Bilka.dk category page
2. Scrolls to load dynamic content
3. Extracts product data (name, prices, discounts)
4. Processes and validates data
5. Stores in database with timestamp
```

### 4. **Error Handling**
- Retries failed requests (up to 3 times)
- Handles timeouts gracefully
- Falls back to mock data if ChromeDriver unavailable

---

## 📊 What Gets Scraped

From each product:
- ✅ Product name
- ✅ Current price
- ✅ Original price (if on sale)
- ✅ Discount percentage
- ✅ Category
- ✅ Product URL
- ✅ Image URL
- ✅ Brand (if available)
- ✅ Availability status
- ✅ Timestamp

---

## ⚙️ Scraping Configuration

Edit `config/settings.yaml`:

```yaml
scraping:
  # Use multiple user agents for variety
  user_agents:
    - "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
  
  # Delays between requests (seconds)
  request_delay_min: 2
  request_delay_max: 5
  
  # Retry failed requests
  max_retries: 3
  
  # Request timeout (seconds)
  timeout: 30
  
  # Run browser in headless mode (no visible window)
  headless: true  # Set to false for debugging
```

Edit `config/scraping_rules.yaml`:

```yaml
selectors:
  # CSS selectors for Bilka.dk elements
  product_container: ".product-card"
  product_name: ".v-card__title"
  price_regular: ".after-price"
  price_sale: ".price-sale"
  discount_badge: ".discount-percentage"
  # ... etc
```

---

## 🐛 Troubleshooting

### Issue: "ChromeDriver not found"

**Solution 1:** Let webdriver-manager handle it (automatic)
```bash
pip install webdriver-manager
```

**Solution 2:** Manual download
1. Check your Chrome version: `chrome://version`
2. Download matching ChromeDriver: https://chromedriver.chromium.org/
3. Add to PATH or place in `drivers/` folder

### Issue: "Permission denied" when starting Chrome

**Solution:**
```bash
# Use mock mode temporarily
export USE_MOCK_SCRAPER=true
python main.py scrape --category electronics --max-products 50
```

### Issue: Scraping is slow

**Reasons:**
- Delays between requests (2-5 seconds) - intentional to be polite
- Page loading time
- Dynamic content scrolling

**Solutions:**
- Reduce `max_products` (scrape fewer products)
- Adjust delays in `config/settings.yaml` (not recommended)
- Run multiple categories in parallel (advanced)

### Issue: No products found

**Causes:**
- Bilka.dk changed their HTML structure
- CSS selectors are outdated
- Network issues
- Being blocked by Bilka.dk

**Solutions:**
1. Check `config/scraping_rules.yaml` selectors
2. Visit Bilka.dk manually to verify site is accessible
3. Check logs in `logs/scraper.log`
4. Update selectors if HTML changed
5. Increase delays between requests

### Issue: "Element not found" errors

**Solution:**
- Increase timeout in `config/settings.yaml`
- Set `headless: false` to debug visually
- Check if selectors match current Bilka.dk HTML

---

## 🔍 Debugging

### Enable Visual Mode

Edit `config/settings.yaml`:
```yaml
scraping:
  headless: false  # Show browser window
```

Then run:
```bash
python main.py scrape --category electronics --max-products 5
```

You'll see Chrome window open and scrape visually.

### Check Logs

```bash
# View scraper logs
cat logs/scraper.log

# Or on Windows
type logs\scraper.log
```

### Test Single Category

```bash
# Test with just 5 products
python main.py scrape --category electronics --max-products 5
```

---

## 📈 Performance Tips

### 1. Start Small
```bash
# Test with 10 products first
python main.py scrape --category electronics --max-products 10
```

### 2. Scrape During Off-Peak Hours
- Late evening or early morning (local time)
- Reduces load on Bilka.dk servers

### 3. Use Appropriate Delays
```yaml
# In config/settings.yaml
request_delay_min: 3  # Increase for better stability
request_delay_max: 7
```

### 4. Monitor Resource Usage
- Chrome can use significant RAM
- Close other applications if needed

---

## 🚀 Advanced Usage

### Scrape All Categories

```bash
python main.py scrape --category all --max-products 50
```

### Automated Daily Scraping

**Windows Task Scheduler:**
```powershell
# Create a scheduled task
schtasks /create /tn "Bilka Scraper" /tr "python C:\path\to\main.py scrape --category all --max-products 100" /sc daily /st 02:00
```

**Linux Cron:**
```bash
# Add to crontab
0 2 * * * cd /path/to/Bilka-Web-Scraper && python main.py scrape --category all --max-products 100
```

### Custom Scraping Script

```python
from src.scraper.bilka_scraper import BilkaScraper
from src.data.storage import create_data_storage

# Initialize
scraper = BilkaScraper()
storage = create_data_storage()

# Scrape
products = scraper.scrape_category('electronics', max_products=100)

# Process and store
from src.data.processor import process_products
processed = process_products(products)
storage.store_multiple_products(processed)

print(f"Scraped {len(products)} products")
```

---

## ⚖️ Legal & Ethical Considerations

### Be Respectful
- ✅ Use reasonable delays between requests
- ✅ Don't overload Bilka.dk servers
- ✅ Respect robots.txt
- ✅ Don't scrape personal data

### Check Terms of Service
- Review Bilka.dk terms of service
- Ensure compliance with local laws
- Use scraped data responsibly

### Rate Limiting
```yaml
# Default settings are conservative
request_delay_min: 2  # seconds
request_delay_max: 5  # seconds
```

---

## 📞 Support

### If Real Scraping Doesn't Work

1. **Check ChromeDriver:**
   ```bash
   python -c "from selenium import webdriver; driver = webdriver.Chrome(); print('OK'); driver.quit()"
   ```

2. **Verify Selectors:**
   - Visit Bilka.dk
   - Inspect HTML elements
   - Update `config/scraping_rules.yaml` if needed

3. **Use Mock Mode:**
   ```bash
   export USE_MOCK_SCRAPER=true
   ```

4. **Check Issues:**
   - GitHub Issues: https://github.com/Diffmayn/Bilka-Web-Scraper/issues

---

## ✅ Success Checklist

- [ ] Python 3.11+ installed
- [ ] Chrome browser installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database initialized (`python main.py init`)
- [ ] ChromeDriver working (automatic via webdriver-manager)
- [ ] Config files reviewed
- [ ] Test scraping successful (5-10 products)
- [ ] Dashboard launches (`streamlit run streamlit_app.py`)
- [ ] Real data visible in dashboard

---

**You're now ready to scrape real data from Bilka.dk! 🎉**

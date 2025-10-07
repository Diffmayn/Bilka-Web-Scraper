# 🏠 Local Hosting Setup Guide

## Why Host Locally?

✅ **Works with Real Chrome** - No bot detection issues  
✅ **Faster** - No deployment delays  
✅ **No Limits** - Scrape as much as you need  
✅ **Privacy** - Data stays on your machine  

❌ **Streamlit Cloud Issues**:
- Bilka.dk detects headless Chromium and blocks it
- Cookie consent walls and CAPTCHA
- Cloud IPs flagged as bots

---

## 🚀 Quick Start (Windows)

### 1. One-Time Setup

```powershell
# Install dependencies (if not already done)
pip install -r requirements.txt
```

### 2. Run Dashboard

**Option A: Double-click the batch file**
```
run_local_dashboard.bat
```

**Option B: Command line**
```powershell
streamlit run streamlit_app.py
```

### 3. Access Dashboard

Open your browser to:
```
http://localhost:8501
```

---

## 🔧 Configuration

The app will use **NON-HEADLESS Chrome** by default for local hosting.

Edit `config/settings.yaml`:

```yaml
scraping:
  headless: false  # Set to false for local hosting
  timeout: 30
  max_retries: 3
  request_delay_min: 2
  request_delay_max: 5
```

---

## 📊 Usage Tips

### Running Background Scrapes

You can run scrapes without the dashboard:

```powershell
python main.py --category electronics --max-products 50
```

### Scheduling Automatic Scrapes (Windows Task Scheduler)

1. Open **Task Scheduler**
2. Create **New Task**
3. Set **Trigger**: Daily at 8:00 AM
4. Set **Action**: Run `run_scheduled_scrape.bat`
5. Done! Daily price monitoring

---

## 🛠️ Troubleshooting

### "ChromeDriver not found"
```powershell
# Download ChromeDriver that matches your Chrome version
# Place in: bilka_price_monitor/drivers/chromedriver.exe
```

### "Port 8501 already in use"
```powershell
# Use different port
streamlit run streamlit_app.py --server.port 8502
```

### Dashboard not loading products
1. Check Chrome is working: `python test_chrome.py`
2. Check database: `python verify_config.py`
3. View logs: `logs/scraper.log`

---

## 🌐 Network Access (Optional)

To access from other devices on your network:

```powershell
# Run with network access
streamlit run streamlit_app.py --server.address 0.0.0.0

# Then access from:
# http://YOUR_LOCAL_IP:8501
# Example: http://192.168.1.100:8501
```

---

## 📁 File Locations

- **Database**: `data/bilka_prices.db`
- **Logs**: `logs/scraper.log`
- **Exports**: `data/exports/`
- **Config**: `config/settings.yaml`

---

## 🔄 Auto-Start on Windows Boot (Optional)

1. Press `Win + R`
2. Type: `shell:startup`
3. Copy shortcut to `run_local_dashboard.bat`
4. Dashboard starts automatically on login!

---

## 💾 Backup Your Data

```powershell
# Backup database
copy data\bilka_prices.db data\backups\bilka_prices_%date%.db

# Export to CSV
# Use the dashboard Export tab
```

---

## 🎯 Recommended Workflow

1. **Morning**: Let scheduled scrape run (8:00 AM)
2. **Afternoon**: Open dashboard to view results
3. **Evening**: Check anomaly alerts for great deals
4. **Weekly**: Export data for trend analysis

---

## 🚫 Stop Hosting

Simply close the terminal window or press `CTRL+C`

---

## ⚡ Performance Tips

- **Close Chrome tabs**: Reduces memory usage
- **Limit max_products**: Faster scraping (50-100 products)
- **Use single category**: Focus on what you need
- **Schedule off-peak**: Run at night/early morning

---

## 📞 Need Help?

Check the logs:
```powershell
type logs\scraper.log | more
```

Test components:
```powershell
python test_chrome.py
python verify_config.py
```

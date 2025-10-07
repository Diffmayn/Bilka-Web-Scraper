# 🏠 LOCAL HOSTING - START HERE

This is the **recommended way** to run the Bilka Price Monitor!

## 🚀 Quick Start

### Windows Users:
**Double-click:** `run_local_dashboard.bat`

### Mac/Linux Users:
```bash
streamlit run streamlit_app.py
```

Then open: **http://localhost:8501**

---

## ✅ Why Local Hosting Works Better

| Feature | Streamlit Cloud ❌ | Local Hosting ✅ |
|---------|-------------------|------------------|
| Bot Detection | Blocked by Bilka | Works perfectly |
| Chrome Driver | Headless Chromium | Full Chrome |
| Cookie Handling | Fails | Works |
| Speed | Slow deploys | Instant |
| Data Privacy | Cloud | Your machine |
| Scraping Limits | Restricted | Unlimited |

---

## 📖 Full Setup Guide

See **LOCAL_SETUP.md** for:
- One-time setup
- Scheduling automatic scrapes
- Network access configuration
- Troubleshooting

---

## 🎯 First Time Running?

1. Make sure Chrome is installed
2. Run `python test_chrome.py` to verify ChromeDriver
3. Click `run_local_dashboard.bat`
4. Wait for browser to open to http://localhost:8501
5. Select **Electronics** category
6. Click **"Start Scraping"**
7. Watch products load! 🎉

---

## 🔧 Common Issues

### "No products found"
- Make sure `headless: false` in `config/settings.yaml`
- ChromeDriver should match your Chrome version
- Try running `python quick_test.py` first

### "Port 8501 already in use"
```powershell
streamlit run streamlit_app.py --server.port 8502
```

---

## 📊 What You Get

- ✅ Real-time price monitoring
- ✅ 5 anomaly detection algorithms
- ✅ Interactive dashboard
- ✅ CSV exports
- ✅ Historical data tracking
- ✅ Discount alerts

---

**Ready? Run `run_local_dashboard.bat` now!** 🚀

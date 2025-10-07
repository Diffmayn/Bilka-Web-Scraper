# 🔧 Troubleshooting: "Cannot see dashboard"

## ✅ Quick Fix - Follow These Steps

### Step 1: Install Dependencies
```powershell
cd "c:\Users\248075\.vscode\cli\WEb SCraper\bilka_price_monitor"
python -m pip install sqlalchemy beautifulsoup4 pyyaml pandas numpy scikit-learn selenium streamlit webdriver-manager lxml
```

### Step 2: Start Dashboard
Double-click: **`run_local_dashboard.bat`**

Or run manually:
```powershell
cd "c:\Users\248075\.vscode\cli\WEb SCraper\bilka_price_monitor"
python -m streamlit run streamlit_app.py
```

### Step 3: Open Browser
The browser should open automatically to:
```
http://localhost:8501
```

If it doesn't, manually open that URL in your browser.

---

## 🔍 Common Issues & Solutions

### Issue 1: "No module named 'sqlalchemy'"
**Cause:** Missing dependencies  
**Solution:**
```powershell
python -m pip install sqlalchemy pandas numpy scikit-learn
```

### Issue 2: "Cannot find streamlit_app.py"
**Cause:** Wrong directory  
**Solution:**
```powershell
cd "c:\Users\248075\.vscode\cli\WEb SCraper\bilka_price_monitor"
```

### Issue 3: "Port 8501 already in use"
**Cause:** Streamlit already running  
**Solution:**
```powershell
# Option 1: Kill existing process
Get-Process | Where-Object {$_.MainWindowTitle -like "*Streamlit*"} | Stop-Process

# Option 2: Use different port
python -m streamlit run streamlit_app.py --server.port 8502
```

### Issue 4: Browser doesn't open automatically
**Cause:** Browser settings  
**Solution:** Manually open:
```
http://localhost:8501
```

### Issue 5: "This site can't be reached"
**Cause:** Streamlit not running or crashed  
**Check:**
1. Look at the terminal window - is Streamlit still running?
2. Do you see "You can now view your Streamlit app in your browser"?
3. Try refreshing the browser page (F5)

---

## 🧪 Test Components

### Test 1: Python Version
```powershell
python --version
# Should be Python 3.10 or higher
```

### Test 2: Dependencies Installed
```powershell
python -c "import streamlit, sqlalchemy, selenium; print('✓ All dependencies OK')"
```

### Test 3: Dashboard Imports
```powershell
cd "c:\Users\248075\.vscode\cli\WEb SCraper\bilka_price_monitor"
python -c "from src.ui.dashboard import main; print('✓ Dashboard OK')"
```

### Test 4: Streamlit Version
```powershell
python -m streamlit --version
# Should be 1.28.0 or higher
```

---

## 📋 Complete Reset (Nuclear Option)

If nothing works, try a complete fresh install:

```powershell
# 1. Uninstall all packages
python -m pip uninstall -y streamlit selenium sqlalchemy pandas numpy scikit-learn beautifulsoup4 pyyaml webdriver-manager

# 2. Reinstall everything
python -m pip install streamlit==1.50.0 selenium==4.36.0 sqlalchemy==2.0.43 beautifulsoup4 pyyaml pandas numpy scikit-learn webdriver-manager lxml

# 3. Restart dashboard
cd "c:\Users\248075\.vscode\cli\WEb SCraper\bilka_price_monitor"
python -m streamlit run streamlit_app.py
```

---

## 🖥️ Manual Start (Debug Mode)

For maximum visibility of what's happening:

```powershell
# Navigate to project
cd "c:\Users\248075\.vscode\cli\WEb SCraper\bilka_price_monitor"

# Start Streamlit with verbose output
python -m streamlit run streamlit_app.py --server.port 8501 --logger.level debug

# Watch for error messages in the terminal
```

---

## 📸 What You Should See

### In Terminal:
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### In Browser:
- **Page Title:** "Bilka Price Monitor"
- **4 Tabs:** Scraping Control | Analysis Results | Price History | Export & Reports
- **Sidebar:** Category selection and scraping options

---

## 🆘 Still Not Working?

### Check these files exist:
```powershell
dir streamlit_app.py
dir src\ui\dashboard.py
dir config\settings.yaml
```

### View recent errors:
```powershell
type logs\scraper.log | Select-Object -Last 50
```

### Test basic scraping:
```powershell
python quick_test.py
```

---

## ✅ Success Checklist

- [ ] Python 3.10+ installed
- [ ] All dependencies installed (sqlalchemy, streamlit, etc.)
- [ ] In correct directory (bilka_price_monitor folder)
- [ ] No other Streamlit process running on port 8501
- [ ] Browser allows localhost connections
- [ ] Terminal shows "You can now view your Streamlit app"

---

## 💡 Pro Tips

1. **Keep terminal window open** - If you close it, Streamlit stops
2. **Watch terminal for errors** - Real-time error messages appear there
3. **Use Chrome/Edge** - Better compatibility than other browsers
4. **Refresh browser (F5)** - If page looks broken
5. **Check firewall** - May block localhost connections

---

## 📞 Quick Commands Reference

```powershell
# Start dashboard
run_local_dashboard.bat

# Check status
python -c "import streamlit; print(streamlit.__version__)"

# Test imports
python -c "from src.ui.dashboard import main"

# View logs
type logs\scraper.log

# Kill Streamlit
taskkill /F /IM streamlit.exe
```

---

**Most common fix: Just install SQLAlchemy!**
```powershell
python -m pip install sqlalchemy
```

Then restart the dashboard. 🚀

# Bilka Price Monitor - Simple POC

## 🎯 Perfect for Company Laptops

This simple POC version is designed specifically for corporate environments where you can't install additional applications. It runs entirely locally using only Python and your existing setup.

## ✨ Features

- **🕷️ Real Data Scraping** - Scrapes live product data from BILKA.dk
- **🌐 Web-Based UI** - Interactive dashboard accessible via web browser
- **💾 Smart Storage** - SQLite database limited to ~2000 records for POC performance
- **🧹 Auto-Cleanup** - Automatically removes old data to stay within limits
- **📊 Live Analytics** - Real-time discount analysis and price monitoring
- **🚀 Zero Dependencies** - No Docker, ngrok, or external applications needed

## 🚀 Quick Start (3 Steps)

### Step 1: Setup Dependencies
```bash
# Double-click this file
setup_poc.bat
```
*Installs minimal Python packages needed for the POC*

### Step 2: Run the Application
```bash
# Double-click this file
run_poc.bat
```
*Starts the web application locally*

### Step 3: Open in Browser
```
http://localhost:8501
```
*Access your price monitoring dashboard*

## 🎮 How to Use

### 1. **Scrape Products**
- Select a product category (electronics, home, sports, clothing)
- Choose how many products to scrape (10-100)
- Click "🚀 Scrape Now"
- Watch real data populate your dashboard!

### 2. **View Dashboard**
- **Total Products**: See how many products you've scraped
- **On Sale**: Count of products currently discounted
- **Avg Discount**: Average discount percentage
- **Recent Products**: Browse your latest scraped data

### 3. **Export Data**
- Click "📥 Export to CSV" to download your data
- Perfect for sharing or further analysis

## 🏗️ Technical Details

### Database Management
- **SQLite Database**: `data/bilka_poc.db`
- **Record Limit**: ~2000 products maximum
- **Auto-Cleanup**: Removes data older than 7 days
- **Smart Limiting**: Keeps most recent data when limit is reached

### Data Structure
```sql
-- Products table
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT,
    current_price REAL,
    original_price REAL,
    discount_percentage REAL,
    category TEXT,
    url TEXT,
    image_url TEXT,
    scraped_at TIMESTAMP
);

-- Activity log
CREATE TABLE scrape_log (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP,
    products_found INTEGER,
    status TEXT
);
```

### Performance Optimizations
- **Batch Processing**: Scrapes products in efficient batches
- **Memory Management**: Processes data without excessive memory usage
- **Database Indexing**: Optimized queries for fast dashboard loading
- **Background Processing**: Non-blocking UI during scraping

## 🔧 Files Included

| File | Purpose |
|------|---------|
| `simple_poc.py` | Main web application |
| `run_poc.bat` | Windows launcher script |
| `setup_poc.bat` | Dependency installation |
| `requirements_poc.txt` | Minimal Python packages |
| `test_poc.py` | Verification script |

## 📊 Dashboard Features

### Real-Time Metrics
- Live product counts and statistics
- Discount analysis and trends
- Category breakdown
- Recent scraping activity

### Interactive Controls
- Category selection for targeted scraping
- Adjustable product limits
- Manual refresh options
- Auto-refresh toggle (every 5 minutes)

### Data Visualization
- Sortable product table
- Price formatting (kr currency)
- Discount percentage display
- Timestamp tracking

## 🚨 Limitations (By Design)

### Storage Limits
- **2000 records maximum** - Keeps POC lightweight
- **7-day retention** - Automatic cleanup of old data
- **SQLite only** - No complex database requirements

### Scope
- **Single retailer** - BILKA.dk only
- **4 categories** - Electronics, Home, Sports, Clothing
- **Web interface only** - No API endpoints
- **Local operation** - No cloud deployment

## 🐛 Troubleshooting

### "Module not found" errors
```bash
# Run setup again
setup_poc.bat
```

### Database issues
```bash
# Delete and recreate database
del data\bilka_poc.db
python -c "from simple_poc import SimpleBilkaMonitor; SimpleBilkaMonitor()"
```

### Port 8501 already in use
```bash
# Kill existing process
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Or use different port
streamlit run simple_poc.py --server.port 8502
```

### Slow scraping
- Reduce the number of products to scrape
- Try different categories
- Check your internet connection

## 🔄 Data Flow

```
BILKA.dk → Scraper → Database → Dashboard → Browser
    ↓         ↓         ↓         ↓         ↓
  Real     Selenium  SQLite    Streamlit  Web UI
 Products   Engine   (~2000    Framework  Display
                     records)
```

## 🎯 Success Criteria

✅ **Functional POC** - Working web application
✅ **Real Data** - Live scraping from BILKA.dk
✅ **Performance** - Handles 2000+ records smoothly
✅ **User-Friendly** - Simple web interface
✅ **Self-Contained** - No external dependencies
✅ **Maintainable** - Clean, documented code

## 🚀 Next Steps

### For POC Evaluation
1. **Test scraping** - Try different categories and product counts
2. **Verify data quality** - Check if prices and discounts are accurate
3. **Test performance** - See how it handles the record limit
4. **Share results** - Export data for analysis

### For Production Scaling
1. **Database upgrade** - Move to PostgreSQL/MySQL
2. **Multi-retailer support** - Add other Danish retailers
3. **API development** - REST API for integrations
4. **Cloud deployment** - Heroku/Railway for 24/7 access
5. **Advanced analytics** - ML-based price predictions

## 📞 Support

### Quick Fixes
- Run `python test_poc.py` to verify setup
- Check `data/bilka_poc.db` exists
- Ensure port 8501 is available

### Common Issues
- **Antivirus blocking**: Add Python to exclusions
- **Corporate firewall**: May need IT approval for scraping
- **Python version**: Requires Python 3.10+

---

**🎉 Your Bilka Price Monitor POC is ready for evaluation!**

*Built for corporate environments - no external tools required*
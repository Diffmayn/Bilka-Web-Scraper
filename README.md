# Bilka Price Monitor - Simple POC Version

> **🖥️ Perfect for Company Laptops** - No Docker, ngrok, or external applications required!

A lightweight web-based price monitoring application for BILKA.dk that runs entirely locally. Designed as a Proof of Concept with smart storage limits (~2000 records) for optimal performance.

## 🚀 Quick Start - Simple POC Version

**Perfect for company laptops - No additional installations required!**

### Step 1: Setup (One-time)
```bash
# Double-click this file to install dependencies
setup_poc.bat
```

### Step 2: Run the Web Application
```bash
# Double-click this file to start the web dashboard
run_poc.bat
```

### Step 3: Open in Browser
```
http://localhost:8501
```

**That's it!** Your web-based price monitor is running locally with:
- ✅ Real-time scraping from BILKA.dk
- ✅ Interactive web dashboard
- ✅ No external applications needed
- ✅ Limited to ~2000 records for POC performance
- ✅ Automatic data cleanup

---

## 📖 Detailed POC Documentation

See [`POC_README.md`](POC_README.md) for complete documentation including:
- Feature overview and technical details
- Troubleshooting guide
- Performance optimizations
- Data management strategies

---

## 🚀 Features

- **Advanced Web Scraping**: Selenium-based scraper with stealth capabilities
- **Real-time Analysis**: Deep discount analysis and error detection algorithms
- **Interactive Dashboard**: Streamlit-based UI for data visualization
- **Data Persistence**: SQLite database with SQLAlchemy ORM
- **Comprehensive Validation**: Multi-layered price validation and anomaly detection
- **Export Capabilities**: CSV/Excel export functionality
- **Docker Support**: Containerized deployment ready

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- Chrome WebDriver
- Git

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bilka_price_monitor
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the system**
   ```bash
   python main.py init
   ```

5. **Configure environment** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## 🚀 Quick Start

### 1. Initialize Database
```bash
python main.py init
```

### 2. Run Scraping (with sample data)
```bash
python main.py scrape --category electronics --max-products 100
```

### 3. Start Dashboard
```bash
python main.py dashboard
```
Open http://localhost:8501 in your browser

### 4. Make Dashboard Online (NEW!)
```bash
# Quick online access with one click
./go_online.bat
```
Or follow the [Online Deployment Guide](ONLINE_DEPLOYMENT_GUIDE.md)

### 5. Run Analysis
```bash
python main.py analyze --output analysis_results.json
```

## 📖 Usage

### Command Line Interface

```bash
# Initialize system
python main.py init

# Scrape specific category
python main.py scrape --category electronics --max-products 500

# Scrape all categories
python main.py scrape --category all --max-products 200

# Run discount analysis
python main.py analyze --output results.json

# Run price validation
python main.py validate --output validation.json

# Start dashboard
python main.py dashboard
```

### Python API Usage

```python
from src.scraper.bilka_scraper import BilkaScraper
from src.analysis.discount_analyzer import analyze_product_discounts

# Initialize scraper
scraper = BilkaScraper()

# Scrape products
products = scraper.scrape_category('electronics', max_products=100)

# Analyze discounts
analysis = analyze_product_discounts(products_df)
print(f"Found {len(analysis.potential_errors)} potential errors")
```

## ⚙️ Configuration

### Settings Files

- `config/settings.yaml`: Main configuration
- `config/scraping_rules.yaml`: Scraping selectors and patterns
- `.env`: Environment variables

### Key Configuration Options

```yaml
# settings.yaml
scraping:
  user_agents:
    - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  request_delay_min: 2
  request_delay_max: 5
  max_retries: 3
  timeout: 30

analysis:
  high_discount_threshold: 75
  critical_discount_threshold: 90
  price_error_margin: 0.05
```

## 🏗️ Project Structure

```
bilka_price_monitor/
├── src/
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── bilka_scraper.py       # Main scraping engine
│   │   ├── product_parser.py      # HTML parsing logic
│   │   └── session_manager.py     # Browser session management
│   ├── data/
│   │   ├── __init__.py
│   │   ├── models.py              # Database models
│   │   ├── processor.py           # Data processing utilities
│   │   └── storage.py             # Data persistence layer
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── discount_analyzer.py   # Discount analysis algorithms
│   │   └── price_validator.py     # Price validation logic
│   └── ui/
│       ├── __init__.py
│       └── dashboard.py           # Streamlit dashboard
├── config/
│   ├── settings.yaml
│   └── scraping_rules.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── exports/
├── tests/
├── requirements.txt
├── main.py
├── .env
└── README.md
```

## 📊 Core Components

### 1. Web Scraping Engine (`src/scraper/`)

- **SessionManager**: Handles Chrome WebDriver with anti-detection measures
- **ProductParser**: Extracts product data from HTML using BeautifulSoup
- **BilkaScraper**: Main orchestration class for scraping operations

### 2. Data Layer (`src/data/`)

- **Models**: SQLAlchemy database models
- **Storage**: Data persistence and retrieval
- **Processor**: Data cleaning and normalization

### 3. Analysis Engine (`src/analysis/`)

- **DiscountAnalyzer**: Advanced discount analysis and error detection
- **PriceValidator**: Multi-layered price validation

### 4. User Interface (`src/ui/`)

- **Dashboard**: Interactive Streamlit application

## 🔧 API Reference

### Scraping API

```python
from src.scraper.bilka_scraper import BilkaScraper

scraper = BilkaScraper()

# Scrape single category
products = scraper.scrape_category('electronics', max_products=100)

# Scrape all categories
all_products = scraper.scrape_all_categories(max_products_per_category=100)

# Scrape single product
product = scraper.scrape_single_product('https://bilka.dk/product/12345')
```

### Analysis API

```python
from src.analysis.discount_analyzer import analyze_product_discounts
from src.analysis.price_validator import validate_product_prices

# Analyze discounts
analysis = analyze_product_discounts(products_df)

# Validate prices
validation = validate_product_prices(products_df)
```

### Data Storage API

```python
from src.data.storage import create_data_storage

storage = create_data_storage()

# Store products
results = storage.store_multiple_products(products)

# Query data
stats = storage.get_database_stats()
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_scraper.py
```

## 🚀 Quick Start - Simple POC Version

**Perfect for company laptops - No additional installations required!**

### Step 1: Setup (One-time)
```bash
# Double-click this file to install dependencies
setup_poc.bat
```

### Step 2: Run the Web Application
```bash
# Double-click this file to start the web dashboard
run_poc.bat
```

### Step 3: Open in Browser
```
http://localhost:8501
```

**That's it!** Your web-based price monitor is running locally with:
- ✅ Real-time scraping from BILKA.dk
- ✅ Interactive web dashboard
- ✅ No external applications needed
- ✅ Limited to ~2000 records for POC performance
- ✅ Automatic data cleanup

---

## 🌐 Online Deployment Options

### Can't Install Docker? No Problem!

If you can't install Docker on your company laptop, here are **Docker-free alternatives**:

#### 🚀 Quick Start (No Docker Required)
```bash
# Option 1: Streamlit Cloud (Easiest)
1. Install dependencies: pip install -r requirements_cloud.txt
2. Go to https://share.streamlit.io
3. Connect your GitHub repo
4. Deploy streamlit_app.py

# Option 2: Local + Ngrok (Quick Sharing)
1. Run: go_online_local.bat
2. Download ngrok from https://ngrok.com/download
3. Run: ngrok http 8501
4. Share the HTTPS URL!
```

#### 📖 Complete Docker-Free Guide
See [`DOCKER_FREE_DEPLOYMENT.md`](DOCKER_FREE_DEPLOYMENT.md) for detailed instructions.

### Traditional Docker Deployment
```bash
# If Docker is available
docker-compose up --build
```

---

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t bilka-monitor .

# Run container
docker run -p 8501:8501 bilka-monitor

# Run with docker-compose
docker-compose up
```

### Docker Compose Configuration

```yaml
version: '3.8'
services:
  bilka-monitor:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - DATABASE_URL=sqlite:///data/bilka_prices.db
```

## 🌐 Online Deployment

### Quick Online Access
For immediate online access to your dashboard:

```bash
# Windows: Double-click go_online.bat
./go_online.bat

# Or manually:
docker-compose up --build
ngrok http 8501
```

### Deployment Options

1. **Ngrok (Free, Instant)**: Perfect for testing and sharing
2. **Local Network**: Access from other devices on your network
3. **Cloud Platforms**: Railway, Heroku, DigitalOcean for 24/7 access

📖 **Complete Guide**: See [ONLINE_DEPLOYMENT_GUIDE.md](ONLINE_DEPLOYMENT_GUIDE.md) for detailed instructions.

### Online Features
- ✅ **Secure HTTPS Access** (with ngrok)
- ✅ **Mobile-Friendly Interface**
- ✅ **Real-time Data Updates**
- ✅ **Shareable URLs**
- ✅ **No Installation Required** for viewers

## 📈 Success Metrics

### Immediate Goals
- ✅ Successfully scrape 500+ products from BILKA.dk
- ✅ Identify and flag 10+ potential pricing errors
- ✅ Load time < 3 seconds for dashboard
- ✅ 95%+ scraping success rate

### Performance Benchmarks
- **Scraping Speed**: 50-100 products/minute
- **Analysis Time**: < 30 seconds for 1000 products
- **Dashboard Load**: < 2 seconds
- **Memory Usage**: < 500MB during normal operation

## 🚨 Error Detection Algorithms

### 1. Extreme Discount Detection
- Flags discounts > 90%
- Identifies potential data entry errors

### 2. Price Relationship Validation
- Detects when sale price > regular price
- Validates price consistency

### 3. Statistical Anomaly Detection
- Z-score analysis for outlier detection
- Historical price deviation analysis

### 4. Business Rule Validation
- Round number discount patterns
- High-value item discount limits

## 🔮 Future Enhancements

### Phase 2: Advanced Analytics
- [ ] SAP S4/HANA integration
- [ ] ML-based anomaly detection
- [ ] Multi-retailer support
- [ ] Automated error reporting

### Phase 3: Production Features
- [ ] Alerting and notification system
- [ ] Scheduled scraping jobs
- [ ] API endpoints
- [ ] User authentication

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

## 🔄 Version History

### v1.0.0 (Current)
- Initial release with core scraping functionality
- Basic discount analysis and error detection
- Streamlit dashboard
- SQLite database integration

---

**Built with ❤️ for price monitoring and analysis**
# Bilka Price Monitor - Docker-Free Deployment Guide

## 🌐 Making Your Dashboard Online (Without Docker)

Since Docker installation isn't possible on your company laptop, here are several **Docker-free alternatives** to make your dashboard accessible online.

## 📋 Quick Alternatives

### Option 1: Streamlit Cloud (Easiest - Recommended)
**Best for:** Quick deployment with zero setup

```bash
# 1. Install required packages locally
pip install -r requirements.txt

# 2. Create a streamlit deployment file
# (We'll create this for you)
```

**Deploy Steps:**
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Select `src/ui/dashboard.py` as main file
4. Click Deploy!

---

### Option 2: Local + Ngrok (No Installation Required)
**Best for:** Testing and sharing without any deployment

```bash
# 1. Install dependencies locally
pip install -r requirements.txt

# 2. Run dashboard locally
python main.py dashboard

# 3. In another terminal, create tunnel
# Download ngrok from: https://ngrok.com/download
ngrok http 8501
```

**Access:** Share the ngrok HTTPS URL with anyone!

---

### Option 3: Heroku (Professional Deployment)
**Best for:** Production-ready deployment

```bash
# 1. Install Heroku CLI
# Download from: https://devcenter.heroku.com/articles/heroku-cli

# 2. Login and create app
heroku login
heroku create bilka-monitor-dashboard

# 3. Deploy
git push heroku main
```

---

### Option 4: Railway (Modern Alternative)
**Best for:** Easy deployment with great performance

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and deploy
railway login
railway deploy
```

---

## 🔧 Local Setup (Required for All Options)

### Step 1: Install Python Dependencies
```bash
# Make sure you have Python 3.11+
python --version

# Install all required packages
pip install -r requirements.txt

# Verify installation
python -c "import streamlit, pandas, selenium; print('All packages installed!')"
```

### Step 2: Initialize Database
```bash
# Set up your local database
python main.py init
```

### Step 3: Test Locally
```bash
# Test the dashboard locally first
python main.py dashboard
# Open http://localhost:8501 in your browser
```

---

## 🚀 Streamlit Cloud Deployment (Recommended)

### Why Streamlit Cloud?
- ✅ **Free tier available**
- ✅ **No server management**
- ✅ **Direct Streamlit deployment**
- ✅ **Automatic scaling**
- ✅ **Built-in authentication options**

### Deployment Steps:

1. **Prepare Your Repository**
   ```bash
   # Make sure your code is committed to Git
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create Streamlit App File**
   - We'll create a `streamlit_app.py` in your project root
   - This will be the entry point for Streamlit Cloud

3. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your repository
   - Choose `streamlit_app.py` as the main file
   - Click **Deploy**

### Configuration for Streamlit Cloud:
```python
# streamlit_app.py (we'll create this)
import streamlit as st
from src.ui.dashboard import main as dashboard_main

if __name__ == "__main__":
    dashboard_main()
```

---

## 🌐 Ngrok Tunneling (Quick & Easy)

### Why Ngrok?
- ✅ **No account required for basic use**
- ✅ **HTTPS URLs automatically**
- ✅ **Works behind corporate firewalls**
- ✅ **Real-time tunneling**

### Setup Steps:

1. **Download Ngrok**
   - Go to: https://ngrok.com/download
   - Download the Windows version
   - Extract to a folder (no installation needed)

2. **Start Your Dashboard**
   ```bash
   python main.py dashboard
   ```

3. **Create Tunnel**
   ```bash
   # In another terminal/command prompt
   ngrok http 8501
   ```

4. **Share the URL**
   - Ngrok will give you a URL like: `https://abc123.ngrok.io`
   - Share this with anyone - they can access your dashboard!

### Ngrok Tips:
- **Custom domains:** Sign up for a free account for custom URLs
- **Persistent URLs:** Paid plans offer fixed URLs
- **Analytics:** See who accesses your dashboard

---

## ☁️ Heroku Deployment

### Why Heroku?
- ✅ **Free tier available**
- ✅ **PostgreSQL database included**
- ✅ **Easy scaling**
- ✅ **Professional deployment**

### Deployment Steps:

1. **Install Heroku CLI**
   ```bash
   # Download from: https://devcenter.heroku.com/articles/heroku-cli
   # Or via npm: npm install -g heroku
   ```

2. **Login and Create App**
   ```bash
   heroku login
   heroku create bilka-monitor-dashboard
   ```

3. **Configure Environment**
   ```bash
   heroku config:set STREAMLIT_SERVER_HEADLESS=true
   heroku config:set STREAMLIT_SERVER_ADDRESS=0.0.0.0
   heroku config:set STREAMLIT_SERVER_PORT=$PORT
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **Open Your App**
   ```bash
   heroku open
   ```

---

## 🚂 Railway Deployment

### Why Railway?
- ✅ **Free tier available**
- ✅ **Modern deployment platform**
- ✅ **Great performance**
- ✅ **Easy database integration**

### Deployment Steps:

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and Create Project**
   ```bash
   railway login
   railway create bilka-monitor
   ```

3. **Deploy**
   ```bash
   railway deploy
   ```

4. **Get Your URL**
   ```bash
   railway domain
   ```

---

## 🔧 Environment Configuration

### For All Deployment Methods:

Create a `.env` file with:
```env
# Database
DATABASE_URL=sqlite:///data/bilka_prices.db

# Streamlit Configuration
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_PORT=8501
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Optional: Add password protection
STREAMLIT_SERVER_ENABLE_BASIC_AUTH=true
STREAMLIT_SERVER_BASIC_AUTH_USERNAME=your_username
STREAMLIT_SERVER_BASIC_AUTH_PASSWORD=your_secure_password
```

---

## 📊 Feature Comparison

| Method | Setup Time | Free Tier | Custom Domain | Database | Scaling |
|--------|------------|-----------|---------------|----------|---------|
| Streamlit Cloud | 5 minutes | ✅ | ❌ | ❌ | Auto |
| Ngrok | 2 minutes | ✅ | ❌ | Local | N/A |
| Heroku | 10 minutes | ✅ | ✅ | ✅ | Manual |
| Railway | 5 minutes | ✅ | ✅ | ✅ | Auto |

---

## 🐛 Troubleshooting

### Common Issues:

**"Module not found" errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Database connection issues:**
```bash
# Reinitialize database
python main.py init
```

**Port already in use:**
```bash
# Kill process using port 8501
netstat -ano | findstr :8501
# Note the PID and kill it
```

**Corporate firewall blocking:**
- Try ngrok - it works well behind corporate firewalls
- Ask IT for permission to use specific ports

---

## 🎯 Recommendation

**For your situation (company laptop):**

1. **First try:** Streamlit Cloud - Easiest and fastest
2. **Backup option:** Local + ngrok - No deployment needed
3. **Professional:** Heroku or Railway - For production use

---

**Your Bilka Price Monitor dashboard can be online in minutes without Docker! 🚀**

Choose the method that works best with your corporate environment.
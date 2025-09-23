# Bilka Price Monitor - Online Dashboard Deployment Guide

## 🌐 Making Your Dashboard Accessible Online

Your Bilka Price Monitor dashboard can now be accessed online through several methods. Choose the option that best fits your needs.

## 📋 Quick Start Options

### Option 1: Docker + Ngrok (Recommended for Testing)
**Best for:** Quick testing and sharing with others

```bash
# 1. Start the dashboard in Docker
docker-compose up --build

# 2. In a new terminal, install ngrok (one-time)
# Download from: https://ngrok.com/download

# 3. Create secure tunnel to your dashboard
ngrok http 8501

# 4. Copy the HTTPS URL from ngrok output
# Example: https://abc123.ngrok.io
```

**Access:** Share the ngrok HTTPS URL with anyone - they'll see your live dashboard!

---

### Option 2: Local Network Access
**Best for:** Accessing from other devices on your network

```bash
# Start the dashboard
docker-compose up --build
```

**Access:**
- **Your computer:** http://localhost:8501
- **Other devices:** http://YOUR_IP_ADDRESS:8501

**Find your IP address:**
- Windows: `ipconfig` (look for IPv4 Address)
- Linux/Mac: `ifconfig` or `ip addr`

---

### Option 3: Cloud Deployment (Production)
**Best for:** 24/7 access from anywhere

#### A) Deploy to Railway (Free tier available)
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and create project
railway login
railway create bilka-monitor

# 3. Deploy
railway deploy

# 4. Get your URL
railway domain
```

#### B) Deploy to Heroku
```bash
# 1. Install Heroku CLI
# Download from: https://devcenter.heroku.com/articles/heroku-cli

# 2. Login and create app
heroku login
heroku create bilka-monitor-dashboard

# 3. Deploy
git push heroku main
```

#### C) Deploy to DigitalOcean App Platform
1. Connect your GitHub repository
2. Choose "Web Service"
3. Set build command: `docker build -f Dockerfile.simple .`
4. Set run command: `python main.py dashboard`

---

## 🔧 Configuration for Online Access

### Environment Variables for Production
Create a `.env` file with:

```env
# Database
DATABASE_URL=sqlite:///data/bilka_prices.db

# Streamlit Configuration
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_PORT=8501
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Security (for production)
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true

# Optional: Add password protection
STREAMLIT_SERVER_ENABLE_BASIC_AUTH=true
STREAMLIT_SERVER_BASIC_AUTH_USERNAME=your_username
STREAMLIT_SERVER_BASIC_AUTH_PASSWORD=your_secure_password
```

### Docker Production Setup
For production deployment, use this enhanced docker-compose:

```yaml
version: '3.8'
services:
  bilka-monitor:
    build:
      context: .
      dockerfile: Dockerfile.simple
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
      - STREAMLIT_SERVER_PORT=8501
      - DATABASE_URL=sqlite:///data/bilka_prices.db
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 🚀 Quick Online Access (Ngrok Method)

### Step 1: Install Ngrok
```bash
# Download from https://ngrok.com/download
# Or using Chocolatey (Windows):
choco install ngrok

# Or using Scoop:
scoop install ngrok
```

### Step 2: Start Your Dashboard
```bash
cd bilka_price_monitor
docker-compose up --build
```

### Step 3: Create Secure Tunnel
```bash
# In a new terminal/command prompt
ngrok http 8501
```

### Step 4: Access Your Dashboard
Ngrok will provide a secure HTTPS URL like:
```
https://abc123.ngrok.io
```

**Share this URL with anyone - they can access your dashboard from anywhere!**

---

## 🔒 Security Considerations

### For Production Deployment:
1. **Enable HTTPS** (ngrok provides this automatically)
2. **Add authentication** using Streamlit's basic auth
3. **Use environment variables** for sensitive data
4. **Regular backups** of your database
5. **Monitor access logs**

### Basic Authentication Setup:
```env
STREAMLIT_SERVER_ENABLE_BASIC_AUTH=true
STREAMLIT_SERVER_BASIC_AUTH_USERNAME=admin
STREAMLIT_SERVER_BASIC_AUTH_PASSWORD=your_secure_password_here
```

---

## 📊 Dashboard Features Available Online

Once deployed, your dashboard includes:

- ✅ **Real-time Data Visualization**
- ✅ **Interactive Charts and Graphs**
- ✅ **Product Search and Filtering**
- ✅ **Price Change Tracking**
- ✅ **Discount Analysis**
- ✅ **Error Detection Reports**
- ✅ **Export Functionality**
- ✅ **Responsive Design** (works on mobile)

---

## 🐛 Troubleshooting

### Dashboard Not Loading:
```bash
# Check if container is running
docker-compose ps

# Check logs
docker-compose logs bilka-monitor

# Restart service
docker-compose restart bilka-monitor
```

### Ngrok Connection Issues:
```bash
# Check ngrok status
ngrok status

# Restart tunnel
ngrok http 8501
```

### Port Already in Use:
```bash
# Kill process using port 8501
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

---

## 🎯 Next Steps

1. **Test locally first:** `docker-compose up --build`
2. **Try ngrok:** Quick online access for testing
3. **Deploy to cloud:** For permanent online access
4. **Add authentication:** Secure your dashboard
5. **Set up monitoring:** Track usage and performance

---

**Your Bilka Price Monitor dashboard is now ready for online access! 🚀**

Choose the deployment method that works best for your needs and start sharing your pricing insights with the world.
#!/usr/bin/env python3
"""
Bilka Price Monitor - Simple Web POC
A lightweight web application for monitoring BILKA.dk prices
No external dependencies required - runs entirely locally
"""

import streamlit as st
import pandas as pd
import sqlite3
import time
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Add project path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our modules - use real or mock scraper based on environment
import os
USE_MOCK = os.getenv('USE_MOCK_SCRAPER', 'false').lower() == 'true'

if USE_MOCK:
    from src.scraper.mock_scraper import MockBilkaScraper as BilkaScraper
    print("⚠️ Using mock scraper (set USE_MOCK_SCRAPER=false for real scraping)")
else:
    from src.scraper.bilka_scraper import BilkaScraper

from src.data.storage import DataStorage
from src.analysis.discount_analyzer import DiscountAnalyzer

# Configuration
MAX_RECORDS = 2000  # Limit database to 2000 records max
DB_PATH = "data/bilka_poc.db"
SCRAPE_INTERVAL = 300  # 5 minutes between scrapes

class SimpleBilkaMonitor:
    """Simple Bilka Price Monitor for POC"""

    def __init__(self):
        self.db_path = DB_PATH
        self.setup_database()
        self.scraper = BilkaScraper()
        self.storage = DataStorage(database_url=f"sqlite:///{self.db_path}")
        self.analyzer = DiscountAnalyzer()

    def setup_database(self):
        """Create simple database schema"""
        os.makedirs("data", exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                current_price REAL,
                original_price REAL,
                discount_percentage REAL,
                category TEXT,
                url TEXT,
                image_url TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                store TEXT DEFAULT 'BILKA'
            )
        ''')

        # Create scrape_log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scrape_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                products_found INTEGER,
                status TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def cleanup_old_data(self):
        """Keep only recent data to stay within limits"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Keep only last 7 days of data
        seven_days_ago = datetime.now() - timedelta(days=7)
        cursor.execute("DELETE FROM products WHERE scraped_at < ?", (seven_days_ago,))

        # If still too many records, keep only the most recent
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]

        if count > MAX_RECORDS:
            # Keep only the most recent records
            keep_count = MAX_RECORDS - 100  # Leave some buffer
            cursor.execute(f"""
                DELETE FROM products
                WHERE id NOT IN (
                    SELECT id FROM products
                    ORDER BY scraped_at DESC
                    LIMIT {keep_count}
                )
            """)

        conn.commit()
        conn.close()

    def scrape_and_store(self, category="electronics", max_products=50):
        """Scrape products and store in database"""
        try:
            # Scrape products
            products = self.scraper.scrape_category(category, max_products=max_products)

            if not products:
                return {"status": "error", "message": "No products found"}

            # Store in database
            stored_count = 0
            conn = sqlite3.connect(self.db_path)

            for product in products:
                try:
                    conn.execute('''
                        INSERT INTO products
                        (name, current_price, original_price, discount_percentage,
                         category, url, image_url, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        product.get('name', ''),
                        product.get('current_price'),
                        product.get('original_price'),
                        product.get('discount_percentage'),
                        category,
                        product.get('url', ''),
                        product.get('image_url', ''),
                        datetime.now()
                    ))
                    stored_count += 1
                except Exception as e:
                    continue  # Skip problematic products

            # Log the scrape
            conn.execute('''
                INSERT INTO scrape_log (products_found, status)
                VALUES (?, ?)
            ''', (stored_count, "success"))

            conn.commit()
            conn.close()

            # Cleanup old data
            self.cleanup_old_data()

            return {
                "status": "success",
                "products_stored": stored_count,
                "total_products": len(products)
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_recent_products(self, limit=100):
        """Get recent products from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('''
                SELECT * FROM products
                ORDER BY scraped_at DESC
                LIMIT ?
            ''', conn, params=(limit,))
            conn.close()
            return df
        except Exception as e:
            return pd.DataFrame()

    def get_dashboard_stats(self):
        """Get statistics for dashboard"""
        try:
            conn = sqlite3.connect(self.db_path)

            # Total products
            total_products = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM products", conn
            ).iloc[0]['count']

            # Products with discounts
            discounted_products = pd.read_sql_query('''
                SELECT COUNT(*) as count FROM products
                WHERE discount_percentage > 0
            ''', conn).iloc[0]['count']

            # Average discount
            avg_discount = pd.read_sql_query('''
                SELECT AVG(discount_percentage) as avg
                FROM products
                WHERE discount_percentage > 0
            ''', conn).iloc[0]['avg']

            # Recent scrapes
            recent_scrapes = pd.read_sql_query('''
                SELECT * FROM scrape_log
                ORDER BY timestamp DESC
                LIMIT 5
            ''', conn)

            conn.close()

            return {
                "total_products": total_products,
                "discounted_products": discounted_products,
                "avg_discount": avg_discount or 0,
                "recent_scrapes": recent_scrapes
            }

        except Exception as e:
            return {
                "total_products": 0,
                "discounted_products": 0,
                "avg_discount": 0,
                "recent_scrapes": pd.DataFrame()
            }

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Bilka Price Monitor - POC",
        page_icon="🛒",
        layout="wide"
    )

    st.title("🛒 Bilka Price Monitor - POC")
    st.markdown("**Web-based price monitoring for BILKA.dk with advanced anomaly detection**")
    st.markdown("---")

    # Initialize monitor
    monitor = SimpleBilkaMonitor()

    # Sidebar for controls
    with st.sidebar:
        st.header("⚙️ Controls")

        # Scrape controls
        st.subheader("🔍 Scrape Products")
        category = st.selectbox(
            "Category",
            ["electronics", "home", "sports", "clothing"],
            help="Select product category to scrape"
        )

        max_products = st.slider(
            "Max Products",
            min_value=10,
            max_value=100,
            value=30,
            help="Maximum products to scrape per session"
        )

        if st.button("🚀 Scrape Now", type="primary"):
            with st.spinner("Scraping products from BILKA.dk..."):
                result = monitor.scrape_and_store(category, max_products)

            if result["status"] == "success":
                st.success(f"✅ Scraped {result['products_stored']} products successfully!")
                st.rerun()
            else:
                st.error(f"❌ Scraping failed: {result['message']}")

        st.markdown("---")

        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh every 5 minutes", value=False)

        # Manual refresh
        if st.button("🔄 Refresh Data"):
            st.rerun()

    # Main content
    col1, col2, col3, col4 = st.columns(4)

    # Get stats
    stats = monitor.get_dashboard_stats()

    with col1:
        st.metric("📊 Total Products", f"{stats['total_products']:,}")

    with col2:
        st.metric("🏷️ On Sale", f"{stats['discounted_products']:,}")

    with col3:
        st.metric("💰 Avg Discount", f"{stats['avg_discount']:.1f}%")

    with col4:
        st.metric("📈 Categories", "4")

    st.markdown("---")

    # Products table
    st.subheader("📋 Recent Products")

    df = monitor.get_recent_products(100)

    if not df.empty:
        # Format the dataframe for display
        display_df = df.copy()
        display_df['current_price'] = display_df['current_price'].apply(
            lambda x: f"kr {x:.2f}" if pd.notna(x) else "N/A"
        )
        display_df['original_price'] = display_df['original_price'].apply(
            lambda x: f"kr {x:.2f}" if pd.notna(x) else "N/A"
        )
        display_df['discount_percentage'] = display_df['discount_percentage'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) and x > 0 else ""
        )
        display_df['scraped_at'] = pd.to_datetime(display_df['scraped_at']).dt.strftime('%Y-%m-%d %H:%M')

        # Rename columns for display
        display_df = display_df.rename(columns={
            'name': 'Product Name',
            'current_price': 'Current Price',
            'original_price': 'Original Price',
            'discount_percentage': 'Discount',
            'category': 'Category',
            'scraped_at': 'Last Updated'
        })

        # Display table
        st.dataframe(
            display_df[['Product Name', 'Current Price', 'Original Price', 'Discount', 'Category', 'Last Updated']],
            use_container_width=True,
            hide_index=True
        )

        # Export functionality
        if st.button("📥 Export to CSV"):
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="bilka_products.csv",
                mime="text/csv"
            )

    else:
        st.info("📭 No products in database yet. Click 'Scrape Now' to get started!")

    # Recent activity
    st.markdown("---")
    st.subheader("📈 Recent Activity")

    if not stats['recent_scrapes'].empty:
        for _, scrape in stats['recent_scrapes'].head(3).iterrows():
            timestamp = pd.to_datetime(scrape['timestamp']).strftime('%H:%M:%S')
            status = "✅" if scrape['status'] == 'success' else "❌"
            st.write(f"{status} {timestamp}: {scrape['products_found']} products scraped")
    else:
        st.write("No recent scraping activity")

    # Footer
    st.markdown("---")
    st.markdown("*Built as a Proof of Concept - Limited to ~2000 records for performance*")

    # Auto-refresh logic
    if auto_refresh:
        time.sleep(SCRAPE_INTERVAL)
        st.rerun()

if __name__ == "__main__":
    main()
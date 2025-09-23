"""
Streamlit Dashboard for Bilka Price Monitor

Interactive web dashboard for monitoring product pricing data,
analyzing discounts, and detecting pricing errors.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Any
import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.storage import DataStorage, create_data_storage
from data.processor import DataProcessor
from analysis.discount_analyzer import DiscountAnalyzer, analyze_product_discounts
from analysis.price_validator import PriceValidator, validate_product_prices
from scraper.bilka_scraper import BilkaScraper


# Configure page
st.set_page_config(
    page_title="Bilka Price Monitor",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data_storage' not in st.session_state:
    st.session_state.data_storage = create_data_storage()

if 'data_processor' not in st.session_state:
    st.session_state.data_processor = DataProcessor()

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

if 'current_data' not in st.session_state:
    st.session_state.current_data = pd.DataFrame()


def load_data() -> pd.DataFrame:
    """Load current pricing data from storage."""
    try:
        # For now, return sample data since we don't have real scraped data yet
        return get_sample_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def get_sample_data() -> pd.DataFrame:
    """Generate sample data for demonstration."""
    import numpy as np

    np.random.seed(42)
    n_products = 1000

    categories = ['Electronics', 'Home', 'Fashion', 'Sports']
    brands = ['Samsung', 'Sony', 'Nike', 'Adidas', 'Apple', 'LG', 'Other']

    data = {
        'external_id': [f'P{i:04d}' for i in range(n_products)],
        'name': [f'Sample Product {i}' for i in range(n_products)],
        'category': np.random.choice(categories, n_products),
        'brand': np.random.choice(brands, n_products),
        'regular_price': np.random.uniform(10, 5000, n_products).round(2),
        'sale_price': None,
        'discount_percentage': None,
        'scraped_at': datetime.now().isoformat()
    }

    df = pd.DataFrame(data)

    # Add sale prices and discounts to some products
    sale_mask = np.random.random(n_products) < 0.3  # 30% of products on sale
    df.loc[sale_mask, 'sale_price'] = (
        df.loc[sale_mask, 'regular_price'] * np.random.uniform(0.5, 0.95, sale_mask.sum())
    ).round(2)

    # Calculate discount percentages
    discount_mask = df['sale_price'].notna()
    df.loc[discount_mask, 'discount_percentage'] = (
        ((df.loc[discount_mask, 'regular_price'] - df.loc[discount_mask, 'sale_price']) /
         df.loc[discount_mask, 'regular_price']) * 100
    ).round(2)

    # Add some anomalies for demonstration
    anomaly_indices = np.random.choice(n_products, size=20, replace=False)
    df.loc[anomaly_indices[:5], 'discount_percentage'] = np.random.uniform(95, 99, 5)  # Extreme discounts
    df.loc[anomaly_indices[5:10], 'sale_price'] = df.loc[anomaly_indices[5:10], 'regular_price'] * 1.1  # Sale > regular
    df.loc[anomaly_indices[10:15], 'regular_price'] = -100  # Negative prices
    df.loc[anomaly_indices[15:], 'discount_percentage'] = -10  # Negative discounts

    return df


def main():
    """Main dashboard function."""

    # Header
    st.title("🛒 Bilka Price Monitor")
    st.markdown("Real-time pricing analysis and discount monitoring for Bilka.dk")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Dashboard Overview", "Product Search", "Discount Analysis", "Scraping Control", "Settings"]
    )

    # Refresh button
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        if st.button("🔄 Refresh"):
            st.session_state.last_refresh = datetime.now()
            st.session_state.current_data = load_data()
            st.rerun()

    with col2:
        st.sidebar.write(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

    # Load data
    if st.session_state.current_data.empty:
        st.session_state.current_data = load_data()

    df = st.session_state.current_data.copy()

    # Route to different pages
    if page == "Dashboard Overview":
        show_dashboard_overview(df)
    elif page == "Product Search":
        show_product_search(df)
    elif page == "Discount Analysis":
        show_discount_analysis(df)
    elif page == "Scraping Control":
        show_scraping_control()
    elif page == "Settings":
        show_settings()


def show_dashboard_overview(df: pd.DataFrame):
    """Show the main dashboard overview."""

    st.header("📊 Dashboard Overview")

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_products = len(df)
        st.metric("Total Products", f"{total_products:,}")

    with col2:
        active_sales = df['sale_price'].notna().sum()
        st.metric("Active Sales", f"{active_sales:,}")

    with col3:
        high_discounts = df[df['discount_percentage'] >= 75]['discount_percentage'].count()
        st.metric("High Discounts (≥75%)", f"{high_discounts:,}")

    with col4:
        # Count potential errors
        errors = 0
        if not df.empty:
            errors += (df['discount_percentage'] > 90).sum()  # Extreme discounts
            errors += (df['discount_percentage'] < 0).sum()  # Negative discounts
            errors += ((df['sale_price'].notna()) & (df['regular_price'].notna()) &
                      (df['sale_price'] > df['regular_price'])).sum()  # Sale > regular
            errors += (df['regular_price'] < 0).sum()  # Negative prices
        st.metric("Potential Errors", f"{errors:,}")

    # Charts section
    st.subheader("📈 Analysis Charts")

    col1, col2 = st.columns(2)

    with col1:
        # Discount distribution histogram
        st.subheader("Discount Distribution")
        discount_data = df[df['discount_percentage'].notna()]

        if not discount_data.empty:
            fig = px.histogram(
                discount_data,
                x='discount_percentage',
                nbins=20,
                title="Distribution of Discount Percentages",
                labels={'discount_percentage': 'Discount %', 'count': 'Number of Products'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No discount data available")

    with col2:
        # Price vs Discount scatter plot
        st.subheader("Price vs Discount Analysis")
        plot_data = df[(df['regular_price'].notna()) & (df['discount_percentage'].notna())]

        if not plot_data.empty:
            fig = px.scatter(
                plot_data,
                x='regular_price',
                y='discount_percentage',
                color='category',
                title="Regular Price vs Discount Percentage",
                labels={
                    'regular_price': 'Regular Price (DKK)',
                    'discount_percentage': 'Discount %',
                    'category': 'Category'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insufficient data for scatter plot")

    # Category breakdown
    st.subheader("📊 Category Analysis")

    if not df.empty:
        category_stats = df.groupby('category').agg({
            'external_id': 'count',
            'regular_price': 'mean',
            'discount_percentage': lambda x: x.notna().sum()
        }).round(2)

        category_stats.columns = ['Product Count', 'Avg Price', 'Products on Sale']
        category_stats = category_stats.reset_index()

        # Bar chart for category comparison
        fig = px.bar(
            category_stats,
            x='category',
            y='Product Count',
            title="Products by Category",
            color='category'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Display category table
        st.dataframe(category_stats, use_container_width=True)
    else:
        st.info("No category data available")


def show_product_search(df: pd.DataFrame):
    """Show product search and filtering interface."""

    st.header("🔍 Product Search")

    # Search and filter controls
    col1, col2, col3 = st.columns(3)

    with col1:
        search_term = st.text_input("Search products", placeholder="Enter product name...")

    with col2:
        category_filter = st.multiselect(
            "Filter by Category",
            options=df['category'].unique() if not df.empty else [],
            default=[]
        )

    with col3:
        price_range = st.slider(
            "Price Range (DKK)",
            min_value=0,
            max_value=int(df['regular_price'].max()) if not df.empty else 1000,
            value=(0, 1000)
        )

    # Apply filters
    filtered_df = df.copy()

    if search_term:
        filtered_df = filtered_df[
            filtered_df['name'].str.contains(search_term, case=False, na=False)
        ]

    if category_filter:
        filtered_df = filtered_df[filtered_df['category'].isin(category_filter)]

    filtered_df = filtered_df[
        (filtered_df['regular_price'] >= price_range[0]) &
        (filtered_df['regular_price'] <= price_range[1])
    ]

    # Display results
    st.subheader(f"Search Results ({len(filtered_df)} products)")

    if not filtered_df.empty:
        # Format display columns
        display_df = filtered_df[[
            'external_id', 'name', 'category', 'brand',
            'regular_price', 'sale_price', 'discount_percentage'
        ]].copy()

        # Format prices
        display_df['regular_price'] = display_df['regular_price'].apply(
            lambda x: f"DKK {x:,.2f}" if pd.notna(x) else "N/A"
        )
        display_df['sale_price'] = display_df['sale_price'].apply(
            lambda x: f"DKK {x:,.2f}" if pd.notna(x) else "N/A"
        )
        display_df['discount_percentage'] = display_df['discount_percentage'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )

        # Rename columns for display
        display_df.columns = [
            'Product ID', 'Name', 'Category', 'Brand',
            'Regular Price', 'Sale Price', 'Discount'
        ]

        st.dataframe(display_df, use_container_width=True)

        # Export option
        if st.button("📥 Export Results to CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"bilka_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No products match the search criteria")


def show_discount_analysis(df: pd.DataFrame):
    """Show detailed discount analysis."""

    st.header("💰 Discount Analysis")

    if df.empty:
        st.warning("No data available for analysis")
        return

    # Run discount analysis
    try:
        analysis = analyze_product_discounts(df)

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Products", f"{analysis.total_products:,}")

        with col2:
            st.metric("Products with Discounts",
                     f"{analysis.products_with_discount:,}",
                     delta=f"{analysis.products_with_discount/analysis.total_products*100:.1f}%")

        with col3:
            st.metric("Average Discount", f"{analysis.average_discount:.1f}%")

        with col4:
            st.metric("Max Discount", f"{analysis.max_discount:.1f}%")

        # Discount distribution
        st.subheader("Discount Distribution")
        if analysis.discount_distribution:
            dist_df = pd.DataFrame(
                list(analysis.discount_distribution.items()),
                columns=['Discount Range', 'Count']
            )

            fig = px.bar(
                dist_df,
                x='Discount Range',
                y='Count',
                title="Products by Discount Range"
            )
            st.plotly_chart(fig, use_container_width=True)

        # High discount products table
        if analysis.high_discount_products:
            st.subheader("🚨 High Discount Products (≥75%)")

            high_discount_df = pd.DataFrame(analysis.high_discount_products)
            display_cols = ['product_id', 'name', 'category', 'regular_price',
                          'sale_price', 'discount_percentage', 'discount_severity']

            if all(col in high_discount_df.columns for col in display_cols):
                display_df = high_discount_df[display_cols].copy()
                display_df.columns = ['ID', 'Name', 'Category', 'Regular Price',
                                    'Sale Price', 'Discount %', 'Severity']

                st.dataframe(display_df, use_container_width=True)

        # Potential errors
        if analysis.potential_errors:
            st.subheader("⚠️ Potential Pricing Errors")

            errors_df = pd.DataFrame(analysis.potential_errors)
            if not errors_df.empty:
                # Group by error type
                error_summary = errors_df.groupby('error_type').size().reset_index(name='count')
                error_summary.columns = ['Error Type', 'Count']

                col1, col2 = st.columns(2)

                with col1:
                    st.dataframe(error_summary, use_container_width=True)

                with col2:
                    fig = px.pie(
                        error_summary,
                        values='Count',
                        names='Error Type',
                        title="Error Types Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Show top errors
                st.subheader("Top Errors")
                top_errors = errors_df.head(10)
                st.dataframe(top_errors[[
                    'product_id', 'name', 'error_type', 'severity', 'description'
                ]], use_container_width=True)

    except Exception as e:
        st.error(f"Error in discount analysis: {e}")
        st.info("Please ensure data is properly formatted for analysis")


def show_scraping_control():
    """Show scraping control interface."""

    st.header("🕷️ Scraping Control")

    st.info("🚧 Scraping functionality will be available after setting up the environment and dependencies.")

    # Placeholder controls
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Target Selection")
        category = st.selectbox(
            "Category to Scrape",
            ["Electronics", "Home", "Fashion", "Sports", "All Categories"]
        )

    with col2:
        st.subheader("Scraping Parameters")
        max_products = st.slider("Max Products per Category", 50, 1000, 250)

    with col3:
        st.subheader("Schedule")
        auto_scrape = st.checkbox("Enable Auto Scraping")
        if auto_scrape:
            frequency = st.selectbox(
                "Frequency",
                ["Every 30 minutes", "Every hour", "Every 6 hours", "Daily"]
            )

    # Action buttons
    st.subheader("Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🚀 Start Scraping", type="primary"):
            st.success("Scraping started! (This is a placeholder)")

    with col2:
        if st.button("⏹️ Stop Scraping"):
            st.info("Scraping stopped (This is a placeholder)")

    with col3:
        if st.button("📊 View Last Scrape Results"):
            st.info("Last scrape results will be displayed here")

    # Scraping status
    st.subheader("Scraping Status")
    st.info("Status: Not configured (dependencies need to be installed)")

    # Instructions
    st.subheader("Setup Instructions")
    st.markdown("""
    To enable scraping functionality:

    1. **Install Dependencies**: Run `pip install -r requirements.txt`
    2. **Install Chrome WebDriver**: Download from https://chromedriver.chromium.org/
    3. **Configure Environment**: Copy `.env` and fill in your settings
    4. **Test Connection**: Use the test connection feature

    The scraping system will then be able to:
    - Automatically navigate Bilka.dk
    - Extract product pricing data
    - Detect pricing anomalies
    - Store data in the database
    """)


def show_settings():
    """Show settings and configuration interface."""

    st.header("⚙️ Settings")

    # Data settings
    st.subheader("Data Configuration")
    col1, col2 = st.columns(2)

    with col1:
        refresh_interval = st.slider(
            "Dashboard Refresh Interval (seconds)",
            min_value=30,
            max_value=3600,
            value=300
        )

    with col2:
        max_display_products = st.slider(
            "Max Products to Display",
            min_value=50,
            max_value=5000,
            value=1000
        )

    # Analysis settings
    st.subheader("Analysis Settings")

    col1, col2, col3 = st.columns(3)

    with col1:
        high_discount_threshold = st.slider(
            "High Discount Threshold (%)",
            min_value=50,
            max_value=95,
            value=75
        )

    with col2:
        critical_discount_threshold = st.slider(
            "Critical Discount Threshold (%)",
            min_value=80,
            max_value=99,
            value=90
        )

    with col3:
        price_error_margin = st.slider(
            "Price Error Margin (%)",
            min_value=1,
            max_value=10,
            value=5
        )

    # Export settings
    st.subheader("Export Settings")
    export_format = st.selectbox(
        "Default Export Format",
        ["CSV", "Excel", "JSON"]
    )

    # Save settings button
    if st.button("💾 Save Settings"):
        st.success("Settings saved! (This is a placeholder - settings will be persisted in a future version)")

    # System information
    st.subheader("System Information")
    st.json({
        "version": "1.0.0",
        "python_version": sys.version,
        "streamlit_version": st.__version__,
        "last_refresh": st.session_state.last_refresh.isoformat(),
        "data_points": len(st.session_state.current_data)
    })


if __name__ == "__main__":
    main()
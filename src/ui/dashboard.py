"""
Streamlit Dashboard for Bilka Price Monitor
Interactive UI for monitoring prices and identifying good deals
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scraper.bilka_scraper import BilkaScraper
from src.data.storage import DataStorage, create_data_storage
from src.analysis.discount_analyzer import DiscountAnalyzer
from src.analysis.price_validator import PriceValidator
from src.analysis.anomaly_detector import AnomalyDetector


def main():
    """Main dashboard application"""
    st.set_page_config(
        page_title="Bilka Price Monitor",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🛒 Bilka Price Monitor")
    st.markdown("**Advanced Price Monitoring & Deal Detection for Bilka.dk**")
    st.markdown("---")

    # Initialize database and components
    try:
        from src.data.storage import initialize_database, reset_database
        
        # Try to initialize normally
        initialize_database()
        
        # Test if schema is correct by trying to query
        test_storage = create_data_storage()
        try:
            test_storage.get_products(limit=1)
        except Exception as schema_error:
            # Schema mismatch detected - recreate database
            st.warning(f"⚠️ Detected old database schema. Recreating database...")
            reset_database()
            initialize_database()
            st.success("✅ Database schema updated!")
            
    except Exception as e:
        st.error(f"❌ Database initialization error: {e}")
    
    storage = create_data_storage()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Controls")

        # Scraping section
        st.subheader("🔍 Scrape Products")
        category = st.selectbox(
            "Category",
            ["electronics", "home", "fashion", "sports"],
            help="Select product category to scrape from Bilka.dk"
        )

        max_products = st.slider(
            "Max Products",
            min_value=10,
            max_value=200,
            value=50,
            step=10,
            help="Maximum number of products to scrape from Bilka.dk"
        )

        if st.button("🚀 Start Scraping", type="primary"):
            scrape_products(category, max_products, storage)

        st.markdown("---")

        # Analysis section
        st.subheader("📊 Analysis Options")
        min_confidence = st.slider(
            "Anomaly Confidence",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Minimum confidence score for anomaly detection"
        )

        show_suspicious_only = st.checkbox(
            "Show Suspicious Deals Only",
            value=False,
            help="Filter to show only potentially suspicious deals"
        )

        st.markdown("---")
        st.subheader("ℹ️ About")
        st.info(
            "This tool scrapes Bilka.dk and identifies **unnaturally good deals** using "
            "5 advanced detection algorithms:\n\n"
            "• Statistical outlier detection\n"
            "• Fake discount detection\n"
            "• Too-good-to-be-true analysis\n"
            "• Price manipulation detection\n"
            "• IQR method analysis"
        )

    # Main content
    display_dashboard(storage, min_confidence, show_suspicious_only)


def scrape_products(category: str, max_products: int, storage: DataStorage):
    """Scrape products and store in database"""
    
    # Create expandable section for debug logs
    debug_expander = st.expander("🔍 Debug Logs", expanded=False)
    
    with st.spinner(f"Scraping {max_products} products from Bilka.dk ({category})..."):
        try:
            # Check if we should use mock scraper (for testing or when ChromeDriver unavailable)
            import os
            use_mock = os.getenv('USE_MOCK_SCRAPER', 'false').lower() == 'true'
            
            with debug_expander:
                st.text(f"Category: {category}")
                st.text(f"Max products: {max_products}")
                st.text(f"Use mock: {use_mock}")
            
            if use_mock:
                st.warning("⚠️ Using mock data (ChromeDriver not available). Set USE_MOCK_SCRAPER=false for real scraping.")
                from src.scraper.mock_scraper import MockBilkaScraper
                scraper = MockBilkaScraper()
            else:
                # Use real scraper
                st.info("🌐 Using real web scraper (BilkaScraper)")
                from src.scraper.bilka_scraper import BilkaScraper
                scraper = BilkaScraper()
                
                with debug_expander:
                    st.text(f"Base URL: {scraper.base_url}")
                    st.text(f"Available categories: {list(scraper.categories.keys())}")
                    if category in scraper.categories:
                        st.text(f"Category path: {scraper.categories[category]}")
                        st.text(f"Full URL: {scraper.base_url}{scraper.categories[category]}")
                    st.text(f"Selector: {scraper.parser.selectors.get('product_container', 'NOT SET')}")

            # Scrape products
            st.info(f"🔄 Starting scrape...")
            with debug_expander:
                st.text("Calling scraper.scrape_category()...")
                st.text(f"Category: {category}, Max: {max_products}")
            
            try:
                products = scraper.scrape_category(category, max_products)
                
                with debug_expander:
                    st.text(f"Scraper returned {len(products)} products")
                    if len(products) > 0:
                        st.text(f"First product: {products[0].get('name', 'NO NAME')[:50]}")
                    else:
                        st.text("⚠️ No products returned from scraper!")
                        st.text("This usually means ChromeDriver didn't start properly")
                        st.text("Try running: python test_scraper_from_dashboard.py")
            except Exception as scrape_error:
                with debug_expander:
                    st.text(f"❌ Scrape exception: {scrape_error}")
                    import traceback
                    st.text(traceback.format_exc())
                products = []

            if products:
                # Store in database
                st.info(f"💾 Storing {len(products)} products...")
                from src.data.processor import process_products
                processed = process_products(products)
                results = storage.store_multiple_products(processed)

                st.success(f"✅ Scraped and stored {results['successful']} products!")

                if results['failed'] > 0:
                    st.warning(f"⚠️ {results['failed']} products failed to store")

                # Log the scrape
                storage.log_scrape({
                    'category': category,
                    'products_found': len(products),
                    'products_stored': results['successful'],
                    'status': 'success',
                    'completed_at': datetime.now()
                })

                st.rerun()
            else:
                st.error("❌ No products found")
                st.error("Please check the '🔍 Debug Logs' section above for details")
                
                # Additional troubleshooting info
                st.warning("""
                **⚠️ ChromeDriver/Streamlit Compatibility Issue**
                
                The scraper works from command line but fails in Streamlit.
                This is a known issue with Selenium in Streamlit's execution model.
                """)
                
                st.info("""
                **✅ WORKAROUND - Use Command Line:**
                
                1. Open PowerShell in project folder
                2. Run: `python main.py --category electronics --max-products 50`
                3. Return to this dashboard to view results
                
                Or use the test script:
                ```
                python test_scraper_from_dashboard.py
                ```
                """)
                
                st.info("""
                **Other possible causes:**
                1. ChromeDriver not starting properly in Streamlit context
                2. Bilka.dk changed their HTML structure
                3. Cookie consent blocking page load
                4. CSS selectors are incorrect
                
                **Check Streamlit Cloud logs for detailed error messages**
                """)

        except Exception as e:
            st.error(f"❌ Scraping failed: {e}")
            with debug_expander:
                import traceback
                st.text("Full error trace:")
                st.code(traceback.format_exc())


def display_dashboard(storage: DataStorage, min_confidence: float, show_suspicious_only: bool):
    """Display the main dashboard"""

    # Get products from database
    try:
        products = storage.get_products(limit=500)
    except Exception as e:
        st.error("⚠️ Database not initialized. Click 'Start Scraping' to begin collecting data from Bilka.dk")
        st.info("""
        **Welcome to Bilka Price Monitor! 🛒**
        
        **Advanced Price Monitoring & Deal Detection for Bilka.dk**
        
        This application scrapes real product data from Bilka.dk and uses advanced algorithms to identify:
        - 🚨 Unnaturally good deals (too good to be true)
        - 🎭 Fake discounts with inflated original prices
        - 📊 Statistical price outliers
        - ⚠️ Price manipulation patterns
        
        **To get started:**
        1. Select a category from the sidebar
        2. Choose how many products to scrape (10-200)
        3. Click "🚀 Start Scraping" to collect data from Bilka.dk
        
        **Note:** Real web scraping requires ChromeDriver. If unavailable, the app will use mock data automatically.
        """)
        return

    if not products:
        st.info("""
        **Welcome to Bilka Price Monitor! 🛒**
        
        **Advanced Price Monitoring & Deal Detection for Bilka.dk**
        
        This application scrapes real product data from Bilka.dk and uses advanced algorithms to identify:
        - 🚨 Unnaturally good deals (too good to be true)
        - 🎭 Fake discounts with inflated original prices
        - 📊 Statistical price outliers
        - ⚠️ Price manipulation patterns
        
        **To get started:**
        1. Select a category from the sidebar
        2. Choose how many products to scrape (10-200)
        3. Click "🚀 Start Scraping" to collect data from Bilka.dk
        
        **Note:** Real web scraping requires ChromeDriver. If unavailable, the app will use mock data automatically.
        """)
        return

    # Convert to DataFrame
    df = pd.DataFrame([{
        'name': p.name,
        'category': p.category,
        'current_price': p.current_price,
        'original_price': p.original_price,
        'discount_percentage': p.discount_percentage or 0,
        'url': p.url,
        'scraped_at': p.scraped_at
    } for p in products])

    # Dashboard metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 Total Products", f"{len(df):,}")

    with col2:
        discounted = len(df[df['discount_percentage'] > 0])
        st.metric("🏷️ On Sale", f"{discounted:,}")

    with col3:
        avg_discount = df[df['discount_percentage'] > 0]['discount_percentage'].mean()
        st.metric("💰 Avg Discount", f"{avg_discount:.1f}%")

    with col4:
        high_discount = len(df[df['discount_percentage'] >= 70])
        st.metric("⚡ High Discounts (70%+)", f"{high_discount:,}")

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔥 Suspicious Deals",
        "📊 All Products",
        "📈 Analytics",
        "🚨 Anomalies"
    ])

    with tab1:
        display_suspicious_deals(df, min_confidence)

    with tab2:
        display_all_products(df, show_suspicious_only)

    with tab3:
        display_analytics(df)

    with tab4:
        display_anomalies(df, storage, min_confidence)


def display_suspicious_deals(df: pd.DataFrame, min_confidence: float):
    """Display suspicious deals that are unnaturally good"""
    st.subheader("🔥 Suspicious Deals - Unnaturally Good Offers")
    st.markdown("These deals have been flagged as potentially too good to be true.")

    # Run discount analysis
    analyzer = DiscountAnalyzer()
    analysis = analyzer.analyze(df)

    if analysis.suspicious_deals:
        # Display suspicious deals
        st.write(f"**Found {len(analysis.suspicious_deals)} suspicious deals:**")

        for i, deal in enumerate(analysis.suspicious_deals[:20], 1):
            with st.expander(
                f"#{i} - {deal['name']} - **{deal['discount_percentage']:.1f}% OFF** "
                f"(Suspicion Score: {deal['suspicion_score']}/100)"
            ):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Current Price", f"kr {deal['current_price']:.2f}")
                    st.metric("Original Price", f"kr {deal['original_price']:.2f}")

                with col2:
                    st.metric("Discount", f"{deal['discount_percentage']:.1f}%")
                    st.metric("Suspicion Score", f"{deal['suspicion_score']}/100")

                with col3:
                    st.metric("Deal Quality", f"{deal['deal_quality']:.0f}/100")
                    st.write(f"**Category:** {deal.get('category', 'Unknown')}")

                st.write("**🔍 Why is this suspicious?**")
                for reason in deal['reasons']:
                    st.write(f"- {reason}")

                st.info(f"**💡 Recommendation:** {deal['recommendation']}")

    else:
        st.success("✅ No highly suspicious deals found in current dataset")


def display_all_products(df: pd.DataFrame, show_suspicious_only: bool):
    """Display all products table"""
    st.subheader("📋 Product List")

    if show_suspicious_only:
        df_filtered = df[df['discount_percentage'] >= 70]
        st.write(f"Showing {len(df_filtered)} products with 70%+ discount")
    else:
        df_filtered = df
        st.write(f"Showing all {len(df_filtered)} products")

    # Format for display
    display_df = df_filtered.copy()
    display_df = display_df.sort_values('discount_percentage', ascending=False)

    display_df['current_price'] = display_df['current_price'].apply(
        lambda x: f"kr {x:.2f}" if pd.notna(x) else "N/A"
    )
    display_df['original_price'] = display_df['original_price'].apply(
        lambda x: f"kr {x:.2f}" if pd.notna(x) else "N/A"
    )
    display_df['discount_percentage'] = display_df['discount_percentage'].apply(
        lambda x: f"{x:.1f}%" if x > 0 else "-"
    )

    st.dataframe(
        display_df[['name', 'category', 'current_price', 'original_price', 'discount_percentage']],
        use_container_width=True,
        hide_index=True
    )

    # Export button
    if st.button("📥 Export to CSV"):
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"bilka_products_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


def display_analytics(df: pd.DataFrame):
    """Display analytics and visualizations"""
    st.subheader("📈 Price Analytics")

    # Discount distribution
    st.write("**Discount Distribution**")
    discount_bins = pd.cut(
        df[df['discount_percentage'] > 0]['discount_percentage'],
        bins=[0, 10, 25, 50, 75, 90, 100],
        labels=['0-10%', '10-25%', '25-50%', '50-75%', '75-90%', '90-100%']
    )
    discount_counts = discount_bins.value_counts().sort_index()

    fig_dist = px.bar(
        x=discount_counts.index,
        y=discount_counts.values,
        labels={'x': 'Discount Range', 'y': 'Number of Products'},
        title='Discount Distribution'
    )
    st.plotly_chart(fig_dist, use_container_width=True)

    # Category analysis
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Products by Category**")
        category_counts = df['category'].value_counts()
        fig_cat = px.pie(
            values=category_counts.values,
            names=category_counts.index,
            title='Products by Category'
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with col2:
        st.write("**Average Discount by Category**")
        avg_discount_by_cat = df[df['discount_percentage'] > 0].groupby('category')['discount_percentage'].mean()
        fig_avg = px.bar(
            x=avg_discount_by_cat.index,
            y=avg_discount_by_cat.values,
            labels={'x': 'Category', 'y': 'Average Discount (%)'},
            title='Average Discount by Category'
        )
        st.plotly_chart(fig_avg, use_container_width=True)

    # Price ranges
    st.write("**Price Distribution**")
    fig_price = px.histogram(
        df,
        x='current_price',
        nbins=50,
        title='Current Price Distribution',
        labels={'current_price': 'Price (DKK)'}
    )
    st.plotly_chart(fig_price, use_container_width=True)


def display_anomalies(df: pd.DataFrame, storage: DataStorage, min_confidence: float):
    """Display detected anomalies"""
    st.subheader("🚨 Anomaly Detection Results")
    st.markdown("Advanced analysis to detect fake discounts, price manipulation, and other issues.")

    # Run anomaly detection
    detector = AnomalyDetector()
    anomalies = detector.detect_anomalies(df)

    # Filter by confidence
    anomalies = [a for a in anomalies if a.confidence_score >= min_confidence]

    if anomalies:
        st.write(f"**Found {len(anomalies)} anomalies with confidence >= {min_confidence}:**")

        # Group by anomaly type
        anomaly_types = {}
        for anomaly in anomalies:
            if anomaly.anomaly_type not in anomaly_types:
                anomaly_types[anomaly.anomaly_type] = []
            anomaly_types[anomaly.anomaly_type].append(anomaly)

        # Display by type
        for anomaly_type, type_anomalies in anomaly_types.items():
            with st.expander(f"{anomaly_type.replace('_', ' ').title()} ({len(type_anomalies)} detected)"):
                for anomaly in type_anomalies[:10]:  # Show top 10
                    st.write(f"**{anomaly.product_name}**")
                    st.write(f"- Confidence: {anomaly.confidence_score:.1%}")
                    st.write(f"- Description: {anomaly.description}")
                    if anomaly.current_price:
                        st.write(f"- Current Price: kr {anomaly.current_price:.2f}")
                    if anomaly.discount_percentage:
                        st.write(f"- Discount: {anomaly.discount_percentage:.1f}%")
                    st.write(f"- **{anomaly.recommendation}**")
                    st.write("**Evidence:**")
                    for evidence in anomaly.evidence:
                        st.write(f"  - {evidence}")
                    st.markdown("---")
    else:
        st.success(f"✅ No anomalies detected with confidence >= {min_confidence}")


if __name__ == "__main__":
    main()

"""
Bilka Price Monitor - Main Entry Point

Command-line interface for the Bilka price monitoring system.
"""

import argparse
import sys
import os
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports work consistently.
sys.path.insert(0, str(Path(__file__).parent))

# Check if we should use mock scraper (for testing or when ChromeDriver unavailable)
USE_MOCK_SCRAPER = os.getenv('USE_MOCK_SCRAPER', 'false').lower() == 'true'

if USE_MOCK_SCRAPER:
    from src.scraper.mock_scraper import MockBilkaScraper as BilkaScraper
    print("⚠️ Using Mock Scraper (set USE_MOCK_SCRAPER=false for real web scraping)")
else:
    from src.scraper.bilka_scraper import BilkaScraper
    print("✓ Using Real Web Scraper")

from src.data.storage import initialize_database, create_data_storage
from src.data.processor import process_products
from src.analysis.discount_analyzer import analyze_product_discounts
from src.analysis.price_validator import validate_product_prices


def main():
    """Main entry point for the Bilka Price Monitor."""
    parser = argparse.ArgumentParser(description="Bilka Price Monitor")
    parser.add_argument(
        "command",
        choices=["scrape", "analyze", "validate", "dashboard", "init"],
        help="Command to execute"
    )
    parser.add_argument(
        "--category",
        choices=["electronics", "home", "fashion", "sports", "all"],
        default="all",
        help="Category to scrape (default: all)"
    )
    parser.add_argument(
        "--max-products",
        type=int,
        default=100,
        help="Maximum products to scrape per category (default: 100)"
    )
    parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--output",
        help="Output file for analysis results"
    )

    args = parser.parse_args()

    try:
        if args.command == "init":
            initialize_system()
        elif args.command == "scrape":
            run_scraping(args.category, args.max_products, args.config)
        elif args.command == "analyze":
            run_analysis(args.output)
        elif args.command == "validate":
            run_validation(args.output)
        elif args.command == "dashboard":
            run_dashboard()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def initialize_system():
    """Initialize the system and database."""
    print("Initializing Bilka Price Monitor system...")

    # Initialize database
    initialize_database()
    print("✅ Database initialized")

    # Create data directories
    directories = ["data/raw", "data/processed", "data/exports", "logs"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

    print("🎉 System initialization complete!")


def run_scraping(category: str, max_products: int, config_path: str):
    """Run the scraping process."""
    print(f"Starting scraping for category: {category}")
    print(f"Max products per category: {max_products}")

    scraper = BilkaScraper(config_path=config_path)

    if category == "all":
        results = scraper.scrape_all_categories(max_products)
        total_products = sum(len(products) for products in results.values())
        print(f"✅ Scraped {total_products} products across all categories")

        for cat, products in results.items():
            print(f"  - {cat}: {len(products)} products")

        # Process and store per-category
        data_storage = create_data_storage()
        total_stored = 0
        total_failed = 0
        for cat, products in results.items():
            if not products:
                continue
            processed_products = process_products(products)
            store_results = data_storage.store_multiple_products(processed_products)
            total_stored += store_results.get('successful', 0)
            total_failed += store_results.get('failed', 0)
        print(f"✅ Stored {total_stored} products successfully ({total_failed} failed)")
    else:
        products = scraper.scrape_category(category, max_products)
        print(f"✅ Scraped {len(products)} products from {category}")

        # Process and store the data
        if products:
            processed_products = process_products(products)
            data_storage = create_data_storage()
            results = data_storage.store_multiple_products(processed_products)
            print(f"✅ Stored {results['successful']} products successfully")


def run_analysis(output_file: str = None):
    """Run discount analysis on stored data."""
    print("Running discount analysis...")

    data_storage = create_data_storage()

    import pandas as pd
    products = data_storage.get_products(limit=5000)
    if not products:
        print("⚠️ No products found in database. Run `python main.py scrape ...` first.")
        return

    df = pd.DataFrame([
        {
            'external_id': p.external_id,
            'name': p.name,
            'category': p.category,
            'current_price': p.current_price,
            'original_price': p.original_price,
            'discount_percentage': p.discount_percentage or 0,
            'url': p.url,
            'scraped_at': p.scraped_at,
        }
        for p in products
    ])

    analysis = analyze_product_discounts(df)

    print("📊 Analysis Results:")
    print(f"  Total Products: {analysis.total_products}")
    print(f"  Products with Discounts: {analysis.products_with_discount}")
    print(f"  Average Discount: {analysis.average_discount:.1f}%")
    print(f"  Max Discount: {analysis.max_discount:.1f}%")
    print(f"  Potential Errors: {len(analysis.potential_errors)}")

    if analysis.potential_errors:
        print("\n🚨 Top Errors:")
        for i, error in enumerate(analysis.potential_errors[:5]):
            print(f"  {i+1}. {error['name']}: {error['description']}")

    if output_file:
        # Save analysis results
        import json
        results = {
            'summary': {
                'total_products': analysis.total_products,
                'products_with_discount': analysis.products_with_discount,
                'average_discount': analysis.average_discount,
                'max_discount': analysis.max_discount
            },
            'errors': analysis.potential_errors,
            'high_discount_products': analysis.high_discount_products
        }

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"✅ Analysis results saved to {output_file}")


def run_validation(output_file: str = None):
    """Run price validation on stored data."""
    print("Running price validation...")

    import pandas as pd
    data_storage = create_data_storage()
    products = data_storage.get_products(limit=5000)
    if not products:
        print("⚠️ No products found in database. Run `python main.py scrape ...` first.")
        return

    df = pd.DataFrame([
        {
            'external_id': p.external_id,
            'name': p.name,
            'category': p.category,
            'current_price': p.current_price,
            'original_price': p.original_price,
            'discount_percentage': p.discount_percentage or 0,
            'url': p.url,
            'scraped_at': p.scraped_at,
        }
        for p in products
    ])

    validation_report = validate_product_prices(df)

    print("🔍 Validation Results:")
    print(f"  Total Products: {validation_report.total_products}")
    print(f"  Valid Products: {validation_report.valid_products}")
    print(f"  Invalid Products: {validation_report.invalid_products}")
    print(f"  Validation Rate: {validation_report.valid_products/validation_report.total_products*100:.1f}%")

    if validation_report.anomaly_summary:
        print("\n📋 Error Breakdown:")
        for error_type, count in validation_report.anomaly_summary.items():
            print(f"  {error_type}: {count}")

    if validation_report.recommendations:
        print("\n💡 Recommendations:")
        for rec in validation_report.recommendations:
            print(f"  • {rec}")

    if output_file:
        # Save validation results
        import json
        results = {
            'summary': {
                'total_products': validation_report.total_products,
                'valid_products': validation_report.valid_products,
                'invalid_products': validation_report.invalid_products,
                'validation_rate': validation_report.valid_products/validation_report.total_products*100
            },
            'errors': validation_report.errors,
            'warnings': validation_report.warnings,
            'validation_passed': validation_report.validation_passed
        }

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"✅ Validation results saved to {output_file}")


def run_dashboard():
    """Run the Streamlit dashboard."""
    print("Starting Streamlit dashboard...")
    print("Open your browser to http://localhost:8501")

    try:
        from src.ui.dashboard import main
        main()
    except ImportError as e:
        print(f"❌ Error importing dashboard: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()
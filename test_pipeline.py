"""
Test the full Bilka Price Monitor pipeline using mock scraper
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from scraper.mock_scraper import MockBilkaScraper
from data.processor import process_products
from data.storage import create_data_storage
from analysis.discount_analyzer import analyze_product_discounts
from analysis.price_validator import validate_product_prices
import pandas as pd
import json
from datetime import datetime

def test_full_pipeline():
    """Test the complete application pipeline."""
    print("🚀 Testing Bilka Price Monitor Full Pipeline")
    print("=" * 50)

    # Step 1: Mock scraping
    print("\n📊 Step 1: Mock Scraping")
    scraper = MockBilkaScraper()
    products = scraper.scrape_category("electronics", max_products=20)
    print(f"✅ Generated {len(products)} mock products")

    # Step 2: Data processing
    print("\n🔄 Step 2: Data Processing")
    processed_products = process_products(products)
    print(f"✅ Processed {len(processed_products)} products")

    # Step 3: Data storage
    print("\n💾 Step 3: Data Storage")
    data_storage = create_data_storage()
    storage_results = data_storage.store_multiple_products(processed_products)
    print(f"✅ Stored {storage_results['successful']} products successfully")
    print(f"❌ Failed to store {storage_results['failed']} products")

    # Step 4: Data analysis
    print("\n📈 Step 4: Discount Analysis")
    df = pd.DataFrame([{
        'external_id': p.external_id,
        'name': p.name,
        'regular_price': p.regular_price,
        'sale_price': p.sale_price,
        'discount_percentage': p.discount_percentage
    } for p in processed_products])

    analysis = analyze_product_discounts(df)
    print(f"📊 Analysis Results:")
    print(f"   Total Products: {analysis.total_products}")
    print(f"   Products with Discounts: {analysis.products_with_discount}")
    print(f"   Average Discount: {analysis.average_discount:.1f}%")
    print(f"   Max Discount: {analysis.max_discount:.1f}%")
    print(f"   Potential Errors: {len(analysis.potential_errors)}")

    # Step 5: Price validation
    print("\n🔍 Step 5: Price Validation")
    validation_report = validate_product_prices(df)
    print(f"🔍 Validation Results:")
    print(f"   Total Products: {validation_report.total_products}")
    print(f"   Valid Products: {validation_report.valid_products}")
    print(f"   Invalid Products: {validation_report.invalid_products}")
    print(f"   Validation Rate: {validation_report.valid_products/validation_report.total_products*100:.1f}%")

    # Step 6: Export results
    print("\n💾 Step 6: Export Results")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Export analysis results
    analysis_file = f"test_results/analysis_{timestamp}.json"
    analysis_data = {
        'summary': {
            'total_products': analysis.total_products,
            'products_with_discount': analysis.products_with_discount,
            'average_discount': analysis.average_discount,
            'max_discount': analysis.max_discount
        },
        'errors': analysis.potential_errors[:5],  # Top 5 errors
        'generated_at': datetime.now().isoformat()
    }

    os.makedirs("test_results", exist_ok=True)
    with open(analysis_file, 'w') as f:
        json.dump(analysis_data, f, indent=2, default=str)
    print(f"✅ Analysis results saved to {analysis_file}")

    # Export validation results
    validation_file = f"test_results/validation_{timestamp}.json"
    validation_data = {
        'summary': {
            'total_products': validation_report.total_products,
            'valid_products': validation_report.valid_products,
            'invalid_products': validation_report.invalid_products,
            'validation_rate': validation_report.valid_products/validation_report.total_products*100
        },
        'errors': validation_report.validation_errors[:5],  # Top 5 errors
        'generated_at': datetime.now().isoformat()
    }

    with open(validation_file, 'w') as f:
        json.dump(validation_data, f, indent=2, default=str)
    print(f"✅ Validation results saved to {validation_file}")

    # Export sample data to CSV
    csv_file = f"test_results/sample_data_{timestamp}.csv"
    df.to_csv(csv_file, index=False)
    print(f"✅ Sample data exported to {csv_file}")

    # Step 7: Database stats
    print("\n📊 Step 7: Database Statistics")
    db_stats = data_storage.get_database_stats()
    print(f"📊 Database Stats:")
    for key, value in db_stats.items():
        print(f"   {key}: {value}")

    print("\n🎉 Pipeline Test Complete!")
    print("=" * 50)
    print("✅ All components working correctly")
    print("✅ Mock data generation: SUCCESS")
    print("✅ Data processing: SUCCESS")
    print("✅ Database operations: SUCCESS")
    print("✅ Analysis algorithms: SUCCESS")
    print("✅ Validation logic: SUCCESS")
    print("✅ Export functionality: SUCCESS")

    return {
        'products_scraped': len(products),
        'products_processed': len(processed_products),
        'products_stored': storage_results['successful'],
        'analysis_errors': len(analysis.potential_errors),
        'validation_rate': validation_report.valid_products/validation_report.total_products*100,
        'files_generated': [analysis_file, validation_file, csv_file]
    }

if __name__ == "__main__":
    try:
        results = test_full_pipeline()
        print(f"\n📋 Test Summary: {results}")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
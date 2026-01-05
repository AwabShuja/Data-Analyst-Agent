"""
Data Enrichment Module
Enriches the raw CSV with additional columns: order_id, amount, quantity, product_name
Uses smart generation based on patterns in the data.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime
import yaml
import os


class DataEnricher:
    """Enriches raw order data with realistic transaction details"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.enrichment_config = self.config['enrichment']
        self.seed = 42  # For reproducibility
        random.seed(self.seed)
        np.random.seed(self.seed)
    
    def load_raw_data(self) -> pd.DataFrame:
        """Load the raw CSV file"""
        csv_path = self.config['database']['raw_csv_path']
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df):,} records from {csv_path}")
        return df
    
    def generate_order_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate unique order IDs
        Logic: Sequential IDs starting from 10001
        """
        df['order_id'] = range(10001, 10001 + len(df))
        print(f"✓ Generated {len(df):,} unique order IDs")
        return df
    
    def generate_amounts(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate realistic order amounts based on business category
        Uses configured price ranges per category
        """
        price_ranges = self.enrichment_config['price_ranges']
        default_range = price_ranges['default']
        
        def get_amount(category):
            price_range = price_ranges.get(category, default_range)
            # Use log-normal distribution for realistic pricing
            # Most orders are lower, some are high-value
            amount = np.random.lognormal(
                mean=np.log(sum(price_range) / 2),
                sigma=0.5
            )
            # Clip to range and round
            amount = np.clip(amount, price_range[0], price_range[1])
            return round(amount, 2)
        
        df['amount'] = df['business_category'].apply(get_amount)
        print(f"✓ Generated amounts (Total Revenue: {df['amount'].sum():,.0f})")
        return df
    
    def generate_quantities(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate quantities (1-5 items per order)
        Weighted towards 1-2 items (more realistic)
        """
        qty_range = self.enrichment_config['quantity_range']
        weights = [0.5, 0.3, 0.12, 0.05, 0.03]  # Favor lower quantities
        
        df['quantity'] = np.random.choice(
            range(qty_range[0], qty_range[1] + 1),
            size=len(df),
            p=weights
        )
        print(f"✓ Generated quantities (Avg: {df['quantity'].mean():.2f} items/order)")
        return df
    
    def generate_product_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate product names based on brand and category
        Format: "{Brand} - {Product Type} #{ID}"
        """
        templates = self.enrichment_config['product_templates']
        
        def get_product_name(row):
            category = row['business_category']
            brand = row['brand_name']
            
            # Get category-specific product types
            product_types = templates.get(category, templates.get('Market Place', ['Item']))
            product_type = random.choice(product_types)
            
            # Generate unique product ID (1-999)
            product_id = random.randint(1, 999)
            
            return f"{brand} - {product_type} #{product_id:03d}"
        
        df['product_name'] = df.apply(get_product_name, axis=1)
        print(f"✓ Generated {df['product_name'].nunique():,} unique product names")
        return df
    
    def add_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add useful derived columns"""
        # Extract date components
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.day_name()
        
        # Revenue = amount * quantity
        df['total_revenue'] = df['amount'] * df['quantity']
        
        print(f"✓ Added derived columns (year, month, day_of_week, total_revenue)")
        return df
    
    def enrich_data(self) -> pd.DataFrame:
        """Main enrichment pipeline"""
        print("\n" + "="*60)
        print("🔧 DATA ENRICHMENT PIPELINE")
        print("="*60 + "\n")
        
        df = self.load_raw_data()
        df = self.generate_order_ids(df)
        df = self.generate_amounts(df)
        df = self.generate_quantities(df)
        df = self.generate_product_names(df)
        df = self.add_derived_columns(df)
        
        # Reorder columns for better readability
        column_order = [
            'order_id', 'userid', 'date', 'year', 'month', 'day_of_week',
            'brand_name', 'product_name', 'business_category', 'outlet_type',
            'quantity', 'amount', 'total_revenue'
        ]
        df = df[column_order]
        
        print(f"\n{'='*60}")
        print("✅ ENRICHMENT COMPLETE")
        print(f"{'='*60}")
        print(f"\nFinal Dataset Shape: {df.shape}")
        print(f"Columns: {', '.join(df.columns)}")
        print(f"\nSample Statistics:")
        print(f"  - Total Orders: {len(df):,}")
        print(f"  - Total Revenue: {df['total_revenue'].sum():,.2f}")
        print(f"  - Avg Order Value: {df['total_revenue'].mean():,.2f}")
        print(f"  - Date Range: {df['date'].min()} to {df['date'].max()}")
        
        return df
    
    def save_enriched_data(self, df: pd.DataFrame):
        """Save enriched data to processed folder"""
        output_path = "data/processed/enriched_orders.csv"
        df.to_csv(output_path, index=False)
        print(f"\n💾 Saved enriched data to: {output_path}")
        return output_path


def main():
    """Run data enrichment"""
    enricher = DataEnricher()
    enriched_df = enricher.enrich_data()
    enricher.save_enriched_data(enriched_df)
    
    print("\n" + "="*60)
    print("📊 SAMPLE DATA (First 5 rows)")
    print("="*60)
    print(enriched_df.head().to_string())
    
    print("\n" + "="*60)
    print("📈 DATA QUALITY CHECKS")
    print("="*60)
    print(f"✓ No missing values: {enriched_df.isnull().sum().sum() == 0}")
    print(f"✓ Unique order IDs: {enriched_df['order_id'].nunique() == len(enriched_df)}")
    print(f"✓ Valid amounts: {(enriched_df['amount'] > 0).all()}")
    print(f"✓ Valid quantities: {(enriched_df['quantity'] > 0).all()}")


if __name__ == "__main__":
    main()

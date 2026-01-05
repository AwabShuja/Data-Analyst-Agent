"""
Database Setup Module
Creates a normalized SQLite database from enriched CSV data.

Tables:
- customers: User demographics and info
- categories: Business categories
- brands: Brand information
- products: Product details
- orders: Transaction records (fact table)
"""

import sqlite3
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List
import os


class DatabaseSetup:
    """Creates and populates a normalized SQLite database"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.db_path = self.config['database']['processed_db_path']
        self.enriched_csv = "data/processed/enriched_orders.csv"
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Create database connection"""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Remove old database if exists
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            print(f"🗑️  Removed old database")
        
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"✓ Connected to database: {self.db_path}")
    
    def load_enriched_data(self) -> pd.DataFrame:
        """Load enriched CSV"""
        df = pd.read_csv(self.enriched_csv)
        print(f"✓ Loaded {len(df):,} enriched records")
        return df
    
    def create_categories_table(self, df: pd.DataFrame):
        """Create categories dimension table"""
        self.cursor.execute("""
            CREATE TABLE categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE NOT NULL,
                category_type TEXT
            )
        """)
        
        # Extract unique categories
        categories = df['business_category'].unique()
        category_data = [
            (cat, self._get_category_type(cat)) 
            for cat in categories
        ]
        
        self.cursor.executemany(
            "INSERT INTO categories (category_name, category_type) VALUES (?, ?)",
            category_data
        )
        print(f"✓ Created categories table ({len(categories)} categories)")
    
    def _get_category_type(self, category: str) -> str:
        """Classify category into broader types"""
        if 'Food' in category or 'Restaurant' in category:
            return 'Food & Dining'
        elif 'Fashion' in category or 'Beauty' in category:
            return 'Fashion & Beauty'
        elif 'Health' in category or 'Fitness' in category:
            return 'Health & Wellness'
        elif 'Grocery' in category or 'Store' in category:
            return 'Retail & Grocery'
        else:
            return 'General Marketplace'
    
    def create_brands_table(self, df: pd.DataFrame):
        """Create brands dimension table"""
        self.cursor.execute("""
            CREATE TABLE brands (
                brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_name TEXT UNIQUE NOT NULL,
                primary_category_id INTEGER,
                FOREIGN KEY (primary_category_id) REFERENCES categories(category_id)
            )
        """)
        
        # Get most common category for each brand
        brand_category = df.groupby('brand_name')['business_category'].agg(
            lambda x: x.value_counts().index[0]
        ).reset_index()
        
        # Get category IDs
        category_map = self._get_category_id_map()
        
        brand_data = [
            (row['brand_name'], category_map.get(row['business_category']))
            for _, row in brand_category.iterrows()
        ]
        
        self.cursor.executemany(
            "INSERT INTO brands (brand_name, primary_category_id) VALUES (?, ?)",
            brand_data
        )
        print(f"✓ Created brands table ({len(brand_data)} brands)")
    
    def create_customers_table(self, df: pd.DataFrame):
        """Create customers dimension table"""
        self.cursor.execute("""
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                first_order_date DATE,
                total_orders INTEGER,
                total_spent REAL,
                favorite_category_id INTEGER,
                preferred_outlet_type TEXT,
                FOREIGN KEY (favorite_category_id) REFERENCES categories(category_id)
            )
        """)
        
        # Aggregate customer data
        customer_stats = df.groupby('userid').agg({
            'date': 'min',  # First order date
            'order_id': 'count',  # Total orders
            'total_revenue': 'sum',  # Total spent
            'business_category': lambda x: x.value_counts().index[0],  # Favorite category
            'outlet_type': lambda x: x.value_counts().index[0]  # Preferred outlet
        }).reset_index()
        
        category_map = self._get_category_id_map()
        
        customer_data = [
            (
                row['userid'],
                row['date'],
                row['order_id'],
                row['total_revenue'],
                category_map.get(row['business_category']),
                row['outlet_type']
            )
            for _, row in customer_stats.iterrows()
        ]
        
        self.cursor.executemany(
            """INSERT INTO customers 
               (customer_id, first_order_date, total_orders, total_spent, 
                favorite_category_id, preferred_outlet_type) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            customer_data
        )
        print(f"✓ Created customers table ({len(customer_data):,} customers)")
    
    def create_products_table(self, df: pd.DataFrame):
        """Create products dimension table"""
        self.cursor.execute("""
            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT UNIQUE NOT NULL,
                brand_id INTEGER,
                category_id INTEGER,
                avg_price REAL,
                FOREIGN KEY (brand_id) REFERENCES brands(brand_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
        """)
        
        # Aggregate product data
        product_stats = df.groupby('product_name').agg({
            'brand_name': 'first',
            'business_category': 'first',
            'amount': 'mean'
        }).reset_index()
        
        brand_map = self._get_brand_id_map()
        category_map = self._get_category_id_map()
        
        product_data = [
            (
                row['product_name'],
                brand_map.get(row['brand_name']),
                category_map.get(row['business_category']),
                round(row['amount'], 2)
            )
            for _, row in product_stats.iterrows()
        ]
        
        self.cursor.executemany(
            """INSERT INTO products 
               (product_name, brand_id, category_id, avg_price) 
               VALUES (?, ?, ?, ?)""",
            product_data
        )
        print(f"✓ Created products table ({len(product_data):,} products)")
    
    def create_orders_table(self, df: pd.DataFrame):
        """Create orders fact table"""
        self.cursor.execute("""
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                brand_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                order_date DATE NOT NULL,
                year INTEGER,
                month INTEGER,
                day_of_week TEXT,
                outlet_type TEXT,
                quantity INTEGER,
                unit_price REAL,
                total_amount REAL,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                FOREIGN KEY (brand_id) REFERENCES brands(brand_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
        """)
        
        # Get ID mappings
        product_map = self._get_product_id_map()
        brand_map = self._get_brand_id_map()
        category_map = self._get_category_id_map()
        
        order_data = [
            (
                row['order_id'],
                row['userid'],
                product_map.get(row['product_name']),
                brand_map.get(row['brand_name']),
                category_map.get(row['business_category']),
                row['date'],
                row['year'],
                row['month'],
                row['day_of_week'],
                row['outlet_type'],
                row['quantity'],
                row['amount'],
                row['total_revenue']
            )
            for _, row in df.iterrows()
        ]
        
        self.cursor.executemany(
            """INSERT INTO orders 
               (order_id, customer_id, product_id, brand_id, category_id,
                order_date, year, month, day_of_week, outlet_type,
                quantity, unit_price, total_amount) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            order_data
        )
        print(f"✓ Created orders table ({len(order_data):,} orders)")
    
    def create_indexes(self):
        """Create indexes for better query performance"""
        indexes = [
            "CREATE INDEX idx_orders_customer ON orders(customer_id)",
            "CREATE INDEX idx_orders_date ON orders(order_date)",
            "CREATE INDEX idx_orders_category ON orders(category_id)",
            "CREATE INDEX idx_orders_brand ON orders(brand_id)",
            "CREATE INDEX idx_customers_total_orders ON customers(total_orders)",
        ]
        
        for idx_sql in indexes:
            self.cursor.execute(idx_sql)
        
        print(f"✓ Created {len(indexes)} indexes for performance")
    
    def _get_category_id_map(self) -> Dict[str, int]:
        """Get category name to ID mapping"""
        self.cursor.execute("SELECT category_name, category_id FROM categories")
        return dict(self.cursor.fetchall())
    
    def _get_brand_id_map(self) -> Dict[str, int]:
        """Get brand name to ID mapping"""
        self.cursor.execute("SELECT brand_name, brand_id FROM brands")
        return dict(self.cursor.fetchall())
    
    def _get_product_id_map(self) -> Dict[str, int]:
        """Get product name to ID mapping"""
        self.cursor.execute("SELECT product_name, product_id FROM products")
        return dict(self.cursor.fetchall())
    
    def print_database_stats(self):
        """Print database statistics"""
        print("\n" + "="*60)
        print("📊 DATABASE STATISTICS")
        print("="*60)
        
        tables = ['categories', 'brands', 'products', 'customers', 'orders']
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            print(f"  {table.capitalize():15} : {count:>10,} records")
        
        # Calculate total revenue
        self.cursor.execute("SELECT SUM(total_amount) FROM orders")
        total_revenue = self.cursor.fetchone()[0]
        print(f"\n  Total Revenue   : {total_revenue:>15,.2f}")
        
        # Date range
        self.cursor.execute("SELECT MIN(order_date), MAX(order_date) FROM orders")
        min_date, max_date = self.cursor.fetchone()
        print(f"  Date Range      : {min_date} to {max_date}")
    
    def setup_database(self):
        """Main database setup pipeline"""
        print("\n" + "="*60)
        print("🗄️  DATABASE SETUP PIPELINE")
        print("="*60 + "\n")
        
        self.connect()
        df = self.load_enriched_data()
        
        print("\nCreating normalized tables...")
        self.create_categories_table(df)
        self.create_brands_table(df)
        self.create_customers_table(df)
        self.create_products_table(df)
        self.create_orders_table(df)
        self.create_indexes()
        
        self.conn.commit()
        self.print_database_stats()
        
        print(f"\n{'='*60}")
        print("✅ DATABASE SETUP COMPLETE")
        print(f"{'='*60}")
        print(f"\nDatabase Location: {self.db_path}")
        print(f"Size: {os.path.getsize(self.db_path) / 1024:.2f} KB")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("\n✓ Database connection closed")


def main():
    """Run database setup"""
    db_setup = DatabaseSetup()
    try:
        db_setup.setup_database()
    finally:
        db_setup.close()


if __name__ == "__main__":
    main()

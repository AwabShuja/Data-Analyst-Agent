"""
Database Query Helper
Provides utility functions for querying and inspecting the database.
"""

import sqlite3
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path


class DatabaseHelper:
    """Helper class for database operations"""
    
    def __init__(self, db_path: str = "data/processed/orders.db"):
        """Initialize database connection"""
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame
        
        Args:
            query: SQL query string
            
        Returns:
            pandas DataFrame with query results
        """
        try:
            df = pd.read_sql_query(query, self.conn)
            return df
        except Exception as e:
            print(f"❌ Query Error: {e}")
            return pd.DataFrame()
    
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """Get column information for a table"""
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)
    
    def list_tables(self) -> List[str]:
        """List all tables in database"""
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        df = self.execute_query(query)
        return df['name'].tolist() if not df.empty else []
    
    def get_row_count(self, table_name: str) -> int:
        """Get number of rows in a table"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        df = self.execute_query(query)
        return df['count'].iloc[0] if not df.empty else 0
    
    def preview_table(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """Preview first N rows of a table"""
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.execute_query(query)
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get complete database summary"""
        summary = {
            'tables': {},
            'total_rows': 0
        }
        
        tables = self.list_tables()
        for table in tables:
            row_count = self.get_row_count(table)
            summary['tables'][table] = row_count
            summary['total_rows'] += row_count
        
        return summary
    
    def verify_relationships(self) -> Dict[str, bool]:
        """Verify foreign key relationships"""
        checks = {}
        
        # Check if all orders have valid customer_ids
        query = """
            SELECT COUNT(*) as invalid_count 
            FROM orders o 
            LEFT JOIN customers c ON o.customer_id = c.customer_id 
            WHERE c.customer_id IS NULL
        """
        result = self.execute_query(query)
        checks['orders_customers_fk'] = result['invalid_count'].iloc[0] == 0
        
        # Check if all orders have valid product_ids
        query = """
            SELECT COUNT(*) as invalid_count 
            FROM orders o 
            LEFT JOIN products p ON o.product_id = p.product_id 
            WHERE p.product_id IS NULL
        """
        result = self.execute_query(query)
        checks['orders_products_fk'] = result['invalid_count'].iloc[0] == 0
        
        return checks
    
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def print_database_overview():
    """Print a comprehensive database overview"""
    with DatabaseHelper() as db:
        print("\n" + "="*60)
        print("📊 DATABASE OVERVIEW")
        print("="*60 + "\n")
        
        summary = db.get_database_summary()
        print("Tables:")
        for table, count in summary['tables'].items():
            print(f"  {table:15} : {count:>10,} rows")
        
        print(f"\n  Total Rows      : {summary['total_rows']:>10,}")
        
        print("\n" + "="*60)
        print("🔗 RELATIONSHIP VERIFICATION")
        print("="*60 + "\n")
        
        checks = db.verify_relationships()
        for check, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {check:30} : {status}")
        
        print("\n" + "="*60)
        print("📋 TABLE PREVIEWS")
        print("="*60 + "\n")
        
        for table in db.list_tables():
            print(f"\n{table.upper()}:")
            print("-" * 60)
            preview = db.preview_table(table, limit=3)
            print(preview.to_string(index=False))


if __name__ == "__main__":
    print_database_overview()

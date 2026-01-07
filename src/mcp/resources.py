"""
MCP Resources - Database Schema Exposure
Exposes database schema, statistics, and examples as MCP resources.
"""

import json
from typing import Dict, List, Any
from datetime import datetime


class DatabaseResources:
    """Exposes database information as MCP resources"""
    
    def __init__(self, query_engine):
        """
        Initialize with SafeQueryEngine
        
        Args:
            query_engine: SafeQueryEngine instance
        """
        self.engine = query_engine
    
    def get_all_resources(self) -> List[Dict[str, Any]]:
        """
        Get list of all available MCP resources
        
        Returns:
            List of resource definitions
        """
        return [
            {
                "uri": "db://schema/all",
                "name": "Database Schema",
                "description": "Complete database schema with tables, columns, types, and row counts",
                "mimeType": "application/json"
            },
            {
                "uri": "db://stats/summary",
                "name": "Database Statistics",
                "description": "Database statistics including row counts, query performance, and audit logs",
                "mimeType": "application/json"
            },
            {
                "uri": "db://examples/queries",
                "name": "Example SQL Queries",
                "description": "Sample SQL queries for common analytics questions",
                "mimeType": "application/json"
            },
            {
                "uri": "db://safety/rules",
                "name": "Safety Rules",
                "description": "SQL safety rules and validation constraints",
                "mimeType": "application/json"
            }
        ]
    
    def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read content of a specific resource
        
        Args:
            uri: Resource URI (e.g., "db://schema/all")
            
        Returns:
            Resource content
        """
        if uri == "db://schema/all":
            return self._get_schema_resource()
        elif uri == "db://stats/summary":
            return self._get_stats_resource()
        elif uri == "db://examples/queries":
            return self._get_examples_resource()
        elif uri == "db://safety/rules":
            return self._get_safety_rules_resource()
        else:
            raise ValueError(f"Unknown resource URI: {uri}")
    
    def _get_schema_resource(self) -> Dict[str, Any]:
        """Get complete database schema"""
        schema = self.engine.get_schema_info()
        
        # Enhance schema with more details
        enhanced_schema = {
            "database": {
                "name": "orders.db",
                "type": "SQLite",
                "total_tables": len(schema['tables']),
                "total_rows": schema['total_rows']
            },
            "tables": {}
        }
        
        for table_name, table_info in schema['tables'].items():
            enhanced_schema['tables'][table_name] = {
                "row_count": table_info['row_count'],
                "columns": table_info['columns'],
                "description": self._get_table_description(table_name)
            }
        
        return {
            "uri": "db://schema/all",
            "mimeType": "application/json",
            "content": enhanced_schema
        }
    
    def _get_stats_resource(self) -> Dict[str, Any]:
        """Get database statistics"""
        audit_stats = self.engine.get_audit_stats()
        schema = self.engine.get_schema_info()
        
        stats = {
            "timestamp": datetime.now().isoformat(),
            "database_stats": {
                "total_tables": len(schema['tables']),
                "total_rows": schema['total_rows'],
                "tables": {
                    table_name: info['row_count']
                    for table_name, info in schema['tables'].items()
                }
            },
            "query_stats": audit_stats,
            "performance": {
                "avg_query_time_ms": audit_stats.get('avg_execution_time_ms', 0),
                "total_queries": audit_stats.get('total_queries', 0),
                "success_rate": (
                    audit_stats.get('approved', 0) / audit_stats.get('total_queries', 1) * 100
                    if audit_stats.get('total_queries', 0) > 0 else 0
                )
            }
        }
        
        return {
            "uri": "db://stats/summary",
            "mimeType": "application/json",
            "content": stats
        }
    
    def _get_examples_resource(self) -> Dict[str, Any]:
        """Get example SQL queries"""
        examples = {
            "basic_queries": [
                {
                    "question": "How many total orders do we have?",
                    "sql": "SELECT COUNT(*) as total_orders FROM orders",
                    "difficulty": "easy"
                },
                {
                    "question": "What is the total revenue?",
                    "sql": "SELECT SUM(total_amount) as total_revenue FROM orders",
                    "difficulty": "easy"
                },
                {
                    "question": "What is the average order value?",
                    "sql": "SELECT AVG(total_amount) as avg_order_value FROM orders",
                    "difficulty": "easy"
                }
            ],
            "intermediate_queries": [
                {
                    "question": "What are the top 5 categories by revenue?",
                    "sql": """SELECT c.category_name, 
       SUM(o.total_amount) as revenue,
       COUNT(*) as order_count
FROM orders o
JOIN categories c ON o.category_id = c.category_id
GROUP BY c.category_name
ORDER BY revenue DESC
LIMIT 5""",
                    "difficulty": "medium"
                },
                {
                    "question": "Which customers have spent more than $10,000?",
                    "sql": """SELECT customer_id, 
       total_spent,
       total_orders
FROM customers
WHERE total_spent > 10000
ORDER BY total_spent DESC
LIMIT 10""",
                    "difficulty": "medium"
                },
                {
                    "question": "What is the monthly order trend?",
                    "sql": """SELECT month,
       COUNT(*) as orders,
       SUM(total_amount) as revenue,
       AVG(total_amount) as avg_order_value
FROM orders
GROUP BY month
ORDER BY month
LIMIT 12""",
                    "difficulty": "medium"
                }
            ],
            "advanced_queries": [
                {
                    "question": "What is the customer retention rate by category?",
                    "sql": """SELECT c.category_name,
       COUNT(DISTINCT CASE WHEN cu.total_orders > 1 THEN cu.customer_id END) as repeat_customers,
       COUNT(DISTINCT cu.customer_id) as total_customers,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN cu.total_orders > 1 THEN cu.customer_id END) / 
             COUNT(DISTINCT cu.customer_id), 2) as retention_rate
FROM customers cu
JOIN categories c ON cu.favorite_category_id = c.category_id
GROUP BY c.category_name
ORDER BY retention_rate DESC
LIMIT 10""",
                    "difficulty": "hard"
                },
                {
                    "question": "Which products have declining sales over time?",
                    "sql": """SELECT p.product_name,
       p.category_id,
       COUNT(CASE WHEN o.month = '2023-05' THEN 1 END) as may_sales,
       COUNT(CASE WHEN o.month = '2023-06' THEN 1 END) as june_sales,
       COUNT(CASE WHEN o.month = '2023-07' THEN 1 END) as july_sales
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category_id
HAVING may_sales > june_sales AND june_sales > july_sales
LIMIT 20""",
                    "difficulty": "hard"
                }
            ]
        }
        
        return {
            "uri": "db://examples/queries",
            "mimeType": "application/json",
            "content": examples
        }
    
    def _get_safety_rules_resource(self) -> Dict[str, Any]:
        """Get SQL safety rules"""
        config = self.engine.config['safety']
        
        rules = {
            "validation_rules": {
                "allowed_operations": ["SELECT"],
                "blocked_operations": config['dangerous_keywords'],
                "max_rows_per_query": config['max_rows'],
                "query_timeout_seconds": config['query_timeout_seconds'],
                "tables_requiring_where_clause": config['require_where_tables']
            },
            "auto_corrections": [
                "Adds LIMIT clause if missing",
                f"Enforces maximum LIMIT of {config['max_rows']} rows"
            ],
            "audit_logging": {
                "enabled": config['audit_enabled'],
                "database": config.get('audit_db_path', 'data/processed/query_audit.db'),
                "tracks": [
                    "All query attempts",
                    "Approved queries",
                    "Rejected queries",
                    "Execution errors",
                    "Execution time",
                    "Row counts"
                ]
            }
        }
        
        return {
            "uri": "db://safety/rules",
            "mimeType": "application/json",
            "content": rules
        }
    
    def _get_table_description(self, table_name: str) -> str:
        """Get human-readable table description"""
        descriptions = {
            "orders": "Fact table containing all order transactions with pricing, quantities, and relationships",
            "customers": "Dimension table with customer profiles and aggregated metrics",
            "products": "Dimension table with product catalog including names, brands, and categories",
            "brands": "Dimension table with merchant/brand information",
            "categories": "Dimension table with business categories (Food, Fashion, etc.)"
        }
        return descriptions.get(table_name, f"Table: {table_name}")

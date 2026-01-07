"""
MCP Tools - Database Query Execution
Exposes safe query execution, validation, and data preview as MCP tools.
"""

from typing import Dict, List, Any, Optional
import json


class DatabaseTools:
    """Exposes database operations as MCP tools"""
    
    def __init__(self, query_engine):
        """
        Initialize with SafeQueryEngine
        
        Args:
            query_engine: SafeQueryEngine instance
        """
        self.engine = query_engine
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of all available MCP tools
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "execute_safe_query",
                "description": "Execute a SQL query with safety validation. Only SELECT queries are allowed. Automatically enforces row limits and validates query syntax.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL SELECT query to execute"
                        }
                    },
                    "required": ["sql"]
                }
            },
            {
                "name": "validate_query",
                "description": "Validate a SQL query without executing it. Checks for dangerous operations, validates table/column names, and provides warnings.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL query to validate"
                        }
                    },
                    "required": ["sql"]
                }
            },
            {
                "name": "get_table_preview",
                "description": "Get a preview of data from a specific table. Returns sample rows to understand table structure and content.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to preview"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of rows to return (default: 5, max: 10)",
                            "default": 5
                        }
                    },
                    "required": ["table_name"]
                }
            },
            {
                "name": "get_query_suggestions",
                "description": "Get SQL query suggestions based on a natural language question. Helps formulate correct SQL queries.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Natural language question about the data"
                        }
                    },
                    "required": ["question"]
                }
            }
        ]
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with given arguments
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if tool_name == "execute_safe_query":
            return self._execute_safe_query(arguments)
        elif tool_name == "validate_query":
            return self._validate_query(arguments)
        elif tool_name == "get_table_preview":
            return self._get_table_preview(arguments)
        elif tool_name == "get_query_suggestions":
            return self._get_query_suggestions(arguments)
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
    
    def _execute_safe_query(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL query with safety validation"""
        sql = arguments.get('sql', '')
        
        if not sql:
            return {
                "success": False,
                "error": "SQL query is required"
            }
        
        # Execute query using safe engine
        result = self.engine.execute_query(sql)
        
        if result['success']:
            # Convert DataFrame to dict for JSON serialization
            data_dict = result['data'].to_dict(orient='records')
            
            return {
                "success": True,
                "data": data_dict,
                "metadata": {
                    "row_count": result['row_count'],
                    "execution_time_ms": result['execution_time_ms'],
                    "warnings": result.get('warnings', []),
                    "modified_query": result.get('modified_query')
                }
            }
        else:
            return {
                "success": False,
                "error": result['error'],
                "execution_time_ms": result['execution_time_ms']
            }
    
    def _validate_query(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SQL query without executing"""
        sql = arguments.get('sql', '')
        
        if not sql:
            return {
                "success": False,
                "error": "SQL query is required"
            }
        
        # Validate using safe engine
        validation = self.engine.validate_only(sql)
        
        return {
            "is_valid": validation.is_valid,
            "error_message": validation.error_message,
            "warnings": validation.warnings,
            "modified_query": validation.modified_query
        }
    
    def _get_table_preview(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get preview of table data"""
        table_name = arguments.get('table_name', '')
        limit = min(arguments.get('limit', 5), 10)  # Max 10 rows
        
        if not table_name:
            return {
                "success": False,
                "error": "table_name is required"
            }
        
        try:
            # Get table preview
            preview_df = self.engine.get_table_preview(table_name, limit)
            
            return {
                "success": True,
                "table_name": table_name,
                "data": preview_df.to_dict(orient='records'),
                "columns": list(preview_df.columns),
                "row_count": len(preview_df)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_query_suggestions(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get SQL query suggestions based on question"""
        question = arguments.get('question', '').lower()
        
        if not question:
            return {
                "success": False,
                "error": "question is required"
            }
        
        # Simple keyword-based suggestions
        suggestions = []
        
        # Revenue/sales related
        if any(word in question for word in ['revenue', 'sales', 'total', 'sum']):
            suggestions.append({
                "query": "SELECT SUM(total_amount) as total_revenue FROM orders",
                "description": "Total revenue across all orders"
            })
            suggestions.append({
                "query": """SELECT c.category_name, SUM(o.total_amount) as revenue
FROM orders o
JOIN categories c ON o.category_id = c.category_id
GROUP BY c.category_name
ORDER BY revenue DESC
LIMIT 10""",
                "description": "Revenue by category"
            })
        
        # Count/number related
        if any(word in question for word in ['how many', 'count', 'number of']):
            suggestions.append({
                "query": "SELECT COUNT(*) as total_orders FROM orders",
                "description": "Total number of orders"
            })
            suggestions.append({
                "query": "SELECT COUNT(DISTINCT customer_id) as total_customers FROM customers",
                "description": "Total number of customers"
            })
        
        # Top/best/highest
        if any(word in question for word in ['top', 'best', 'highest', 'most']):
            suggestions.append({
                "query": """SELECT customer_id, total_spent, total_orders
FROM customers
ORDER BY total_spent DESC
LIMIT 10""",
                "description": "Top 10 customers by spending"
            })
            suggestions.append({
                "query": """SELECT c.category_name, COUNT(*) as order_count
FROM orders o
JOIN categories c ON o.category_id = c.category_id
GROUP BY c.category_name
ORDER BY order_count DESC
LIMIT 5""",
                "description": "Top 5 categories by order count"
            })
        
        # Average related
        if any(word in question for word in ['average', 'avg', 'mean']):
            suggestions.append({
                "query": "SELECT AVG(total_amount) as avg_order_value FROM orders",
                "description": "Average order value"
            })
        
        # Customer related
        if 'customer' in question:
            suggestions.append({
                "query": """SELECT COUNT(*) as total_customers,
       SUM(CASE WHEN total_orders > 1 THEN 1 ELSE 0 END) as repeat_customers
FROM customers""",
                "description": "Customer counts and repeat customers"
            })
        
        # Month/time related
        if any(word in question for word in ['month', 'monthly', 'trend', 'time']):
            suggestions.append({
                "query": """SELECT month, COUNT(*) as orders, SUM(total_amount) as revenue
FROM orders
GROUP BY month
ORDER BY month
LIMIT 12""",
                "description": "Monthly order and revenue trend"
            })
        
        # If no specific suggestions, provide general ones
        if not suggestions:
            suggestions = [
                {
                    "query": "SELECT COUNT(*) as total_orders FROM orders",
                    "description": "Total number of orders"
                },
                {
                    "query": "SELECT * FROM orders LIMIT 10",
                    "description": "Sample orders data"
                }
            ]
        
        return {
            "success": True,
            "question": question,
            "suggestions": suggestions[:5]  # Limit to 5 suggestions
        }

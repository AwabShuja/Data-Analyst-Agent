"""
MCP Server - Main Server Implementation
Implements Model Context Protocol server for database access.
"""

import json
from typing import Dict, List, Any, Optional
import yaml

from .resources import DatabaseResources
from .tools import DatabaseTools
from ..safety import SafeQueryEngine


class MCPServer:
    """
    Model Context Protocol Server for Database Access
    
    Provides MCP-compliant interface to database with:
    - Resources: DB schema, statistics, examples
    - Tools: Safe query execution, validation, previews
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize MCP server
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize query engine
        db_path = self.config['database']['processed_db_path']
        self.query_engine = SafeQueryEngine(db_path, self.config)
        
        # Initialize resources and tools
        self.resources = DatabaseResources(self.query_engine)
        self.tools = DatabaseTools(self.query_engine)
        
        # MCP server info
        self.server_info = {
            "name": "AI Data Analyst Database Server",
            "version": "1.0.0",
            "description": "MCP server providing safe access to e-commerce analytics database"
        }
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return self.server_info
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """
        List all available resources
        
        MCP Protocol: resources/list
        
        Returns:
            List of resource definitions
        """
        return self.resources.get_all_resources()
    
    def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read a specific resource
        
        MCP Protocol: resources/read
        
        Args:
            uri: Resource URI (e.g., "db://schema/all")
            
        Returns:
            Resource content
        """
        try:
            return self.resources.read_resource(uri)
        except Exception as e:
            return {
                "error": str(e),
                "uri": uri
            }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools
        
        MCP Protocol: tools/list
        
        Returns:
            List of tool definitions
        """
        return self.tools.get_all_tools()
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a specific tool
        
        MCP Protocol: tools/call
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        try:
            return self.tools.call_tool(tool_name, arguments)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name
            }
    
    def handle_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle MCP protocol request
        
        Args:
            method: MCP method (e.g., "resources/list", "tools/call")
            params: Method parameters
            
        Returns:
            Response data
        """
        params = params or {}
        
        if method == "server/info":
            return self.get_server_info()
        
        elif method == "resources/list":
            return {"resources": self.list_resources()}
        
        elif method == "resources/read":
            uri = params.get('uri')
            if not uri:
                return {"error": "URI is required"}
            return self.read_resource(uri)
        
        elif method == "tools/list":
            return {"tools": self.list_tools()}
        
        elif method == "tools/call":
            tool_name = params.get('name')
            arguments = params.get('arguments', {})
            if not tool_name:
                return {"error": "Tool name is required"}
            return self.call_tool(tool_name, arguments)
        
        else:
            return {"error": f"Unknown method: {method}"}
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get server capabilities
        
        Returns:
            Server capabilities
        """
        return {
            "resources": {
                "supported": True,
                "count": len(self.list_resources())
            },
            "tools": {
                "supported": True,
                "count": len(self.list_tools())
            },
            "prompts": {
                "supported": False
            }
        }
    
    def get_usage_examples(self) -> Dict[str, Any]:
        """
        Get usage examples for the MCP server
        
        Returns:
            Usage examples
        """
        return {
            "list_resources": {
                "method": "resources/list",
                "params": {},
                "description": "Get all available database resources"
            },
            "read_schema": {
                "method": "resources/read",
                "params": {"uri": "db://schema/all"},
                "description": "Read complete database schema"
            },
            "execute_query": {
                "method": "tools/call",
                "params": {
                    "name": "execute_safe_query",
                    "arguments": {
                        "sql": "SELECT COUNT(*) as total FROM orders"
                    }
                },
                "description": "Execute a safe SQL query"
            },
            "validate_query": {
                "method": "tools/call",
                "params": {
                    "name": "validate_query",
                    "arguments": {
                        "sql": "SELECT * FROM orders LIMIT 10"
                    }
                },
                "description": "Validate a SQL query without executing"
            },
            "preview_table": {
                "method": "tools/call",
                "params": {
                    "name": "get_table_preview",
                    "arguments": {
                        "table_name": "orders",
                        "limit": 5
                    }
                },
                "description": "Get preview of table data"
            }
        }
    
    def close(self):
        """Close server and cleanup resources"""
        if self.query_engine:
            self.query_engine.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

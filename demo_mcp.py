"""
MCP Server Usage Example
Shows how to use the MCP server to access database via MCP protocol.
"""

from src.mcp import MCPServer
import json


def demo_mcp_server():
    """Demonstrate MCP server usage"""
    
    print("\n" + "="*60)
    print("MCP SERVER DEMO - Phase 2B")
    print("="*60)
    
    with MCPServer() as server:
        
        # Example 1: Get server info
        print("\n📋 Server Info:")
        info = server.get_server_info()
        print(f"   Name: {info['name']}")
        print(f"   Version: {info['version']}")
        
        # Example 2: List available resources
        print("\n📚 Available Resources:")
        resources = server.list_resources()
        for r in resources:
            print(f"   - {r['uri']}: {r['name']}")
        
        # Example 3: Read database schema
        print("\n🗄️  Database Schema:")
        schema = server.read_resource("db://schema/all")
        print(f"   Total Tables: {schema['content']['database']['total_tables']}")
        print(f"   Total Rows: {schema['content']['database']['total_rows']:,}")
        
        # Example 4: List available tools
        print("\n🔧 Available Tools:")
        tools = server.list_tools()
        for t in tools:
            print(f"   - {t['name']}")
        
        # Example 5: Execute a query via tool
        print("\n🚀 Execute Query:")
        result = server.call_tool("execute_safe_query", {
            "sql": "SELECT COUNT(*) as total, SUM(total_amount) as revenue FROM orders"
        })
        if result['success']:
            print(f"   Success! Rows: {result['metadata']['row_count']}")
            print(f"   Data: {json.dumps(result['data'], indent=4)}")
        
        # Example 6: Get query suggestions
        print("\n💡 Query Suggestions:")
        result = server.call_tool("get_query_suggestions", {
            "question": "top customers"
        })
        if result['success']:
            for i, suggestion in enumerate(result['suggestions'][:2], 1):
                print(f"\n   {i}. {suggestion['description']}")
                print(f"      {suggestion['query'][:70]}...")
        
        print("\n" + "="*60)
        print("✅ MCP Server Ready for LLM Agent Integration")
        print("="*60 + "\n")


if __name__ == "__main__":
    demo_mcp_server()

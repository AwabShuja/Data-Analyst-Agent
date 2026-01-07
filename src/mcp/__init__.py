"""
Model Context Protocol (MCP) Module
Exposes database as MCP resources and safe query execution as MCP tools.
"""

from .server import MCPServer
from .resources import DatabaseResources
from .tools import DatabaseTools

__all__ = ['MCPServer', 'DatabaseResources', 'DatabaseTools']

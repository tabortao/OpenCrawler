"""
MCP (Model Context Protocol) 模块

提供符合 MCP 标准的服务器实现，支持与 Claude Desktop 等 AI 工具的无缝对接。
"""

from app.mcp.server import MCPServer
from app.mcp.protocol import JSONRPCRequest, JSONRPCResponse, JSONRPCNotification
from app.mcp.tools import ToolRegistry, Tool
from app.mcp.resources import ResourceRegistry, Resource
from app.mcp.prompts import PromptRegistry, Prompt

__all__ = [
    "MCPServer",
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCNotification",
    "ToolRegistry",
    "Tool",
    "ResourceRegistry",
    "Resource",
    "PromptRegistry",
    "Prompt",
]

__version__ = "1.0.0"

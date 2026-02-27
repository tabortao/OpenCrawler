"""
MCP Tools 模块

实现 MCP 工具注册和调用功能。
"""

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union
from abc import ABC, abstractmethod

from app.mcp.protocol import JSONRPCResponse, JSONRPCErrorCodes


@dataclass
class ToolInputSchema:
    """工具输入模式"""
    type: str = "object"
    properties: dict[str, Any] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "type": self.type,
            "properties": self.properties,
        }
        if self.required:
            result["required"] = self.required
        return result


@dataclass
class ToolAnnotation:
    """工具注解"""
    title: Optional[str] = None
    read_only_hint: bool = False
    destructive_hint: bool = False
    idempotent_hint: bool = False
    open_world_hint: bool = True
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {}
        if self.title:
            result["title"] = self.title
        if self.read_only_hint:
            result["readOnlyHint"] = self.read_only_hint
        if self.destructive_hint:
            result["destructiveHint"] = self.destructive_hint
        if self.idempotent_hint:
            result["idempotentHint"] = self.idempotent_hint
        if self.open_world_hint:
            result["openWorldHint"] = self.open_world_hint
        return result


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    input_schema: ToolInputSchema
    handler: Callable
    annotations: Optional[ToolAnnotation] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema.to_dict(),
        }
        if self.annotations:
            result["annotations"] = self.annotations.to_dict()
        return result


@dataclass
class TextContent:
    """文本内容"""
    type: str = "text"
    text: str = ""
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "type": self.type,
            "text": self.text,
        }


@dataclass
class ImageContent:
    """图片内容"""
    type: str = "image"
    data: str = ""
    mime_type: str = "image/png"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "type": self.type,
            "data": self.data,
            "mimeType": self.mime_type,
        }


@dataclass
class ResourceContent:
    """资源内容"""
    type: str = "resource"
    resource: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "type": self.type,
            "resource": self.resource,
        }


@dataclass
class ToolResult:
    """工具调用结果"""
    content: list[Union[TextContent, ImageContent, ResourceContent]]
    is_error: bool = False
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "content": [c.to_dict() for c in self.content],
            "isError": self.is_error,
        }
    
    @classmethod
    def text(cls, text: str, is_error: bool = False) -> "ToolResult":
        """创建文本结果"""
        return cls(
            content=[TextContent(text=text)],
            is_error=is_error,
        )
    
    @classmethod
    def error(cls, message: str) -> "ToolResult":
        """创建错误结果"""
        return cls.text(text=message, is_error=True)


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: dict[str, Tool] = {}
    
    def register(
        self,
        name: str,
        description: str,
        input_schema: Optional[ToolInputSchema] = None,
        annotations: Optional[ToolAnnotation] = None,
    ) -> Callable:
        """
        注册工具装饰器
        
        Args:
            name: 工具名称
            description: 工具描述
            input_schema: 输入模式
            annotations: 工具注解
        
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            schema = input_schema or self._infer_schema(func)
            
            tool = Tool(
                name=name,
                description=description,
                input_schema=schema,
                handler=func,
                annotations=annotations,
            )
            self._tools[name] = tool
            return func
        
        return decorator
    
    def register_tool(self, tool: Tool):
        """
        直接注册工具
        
        Args:
            tool: 工具对象
        """
        self._tools[tool.name] = tool
    
    def _infer_schema(self, func: Callable) -> ToolInputSchema:
        """从函数签名推断输入模式"""
        sig = inspect.signature(func)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'cls'):
                continue
            
            prop = {"type": "string"}
            
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    prop["type"] = "integer"
                elif param.annotation == float:
                    prop["type"] = "number"
                elif param.annotation == bool:
                    prop["type"] = "boolean"
                elif param.annotation == list:
                    prop["type"] = "array"
                elif param.annotation == dict:
                    prop["type"] = "object"
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
            
            properties[param_name] = prop
        
        return ToolInputSchema(
            type="object",
            properties=properties,
            required=required,
        )
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        获取工具
        
        Args:
            name: 工具名称
        
        Returns:
            工具对象或 None
        """
        return self._tools.get(name)
    
    def list_tools(self, cursor: Optional[str] = None) -> tuple[list[Tool], Optional[str]]:
        """
        列出工具
        
        Args:
            cursor: 分页游标
        
        Returns:
            (工具列表, 下一页游标)
        """
        return list(self._tools.values()), None
    
    def has_tools(self) -> bool:
        """检查是否有工具"""
        return len(self._tools) > 0
    
    async def call_tool(self, name: str, arguments: dict) -> ToolResult:
        """
        调用工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
        
        Returns:
            工具调用结果
        """
        tool = self.get_tool(name)
        if not tool:
            return ToolResult.error(f"Unknown tool: {name}")
        
        try:
            result = tool.handler(**arguments)
            
            if inspect.isawaitable(result):
                result = await result
            
            if isinstance(result, ToolResult):
                return result
            elif isinstance(result, str):
                return ToolResult.text(result)
            elif isinstance(result, dict):
                import json
                return ToolResult.text(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                return ToolResult.text(str(result))
                
        except TypeError as e:
            return ToolResult.error(f"Invalid arguments: {e}")
        except Exception as e:
            return ToolResult.error(f"Tool execution error: {e}")
    
    def create_list_response(self, cursor: Optional[str] = None) -> dict:
        """
        创建工具列表响应
        
        Args:
            cursor: 分页游标
        
        Returns:
            响应字典
        """
        tools, next_cursor = self.list_tools(cursor)
        result = {
            "tools": [t.to_dict() for t in tools],
        }
        if next_cursor:
            result["nextCursor"] = next_cursor
        return result


class BaseTool(ABC):
    """工具基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @property
    def input_schema(self) -> ToolInputSchema:
        """输入模式"""
        return ToolInputSchema()
    
    @property
    def annotations(self) -> Optional[ToolAnnotation]:
        """工具注解"""
        return None
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass
    
    def to_tool(self) -> Tool:
        """转换为工具对象"""
        return Tool(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            handler=self.execute,
            annotations=self.annotations,
        )

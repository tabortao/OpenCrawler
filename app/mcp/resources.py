"""
MCP Resources 模块

实现 MCP 资源注册和访问功能。
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union
from abc import ABC, abstractmethod

from app.mcp.protocol import JSONRPCErrorCodes


@dataclass
class Resource:
    """资源定义"""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "uri": self.uri,
            "name": self.name,
        }
        if self.description:
            result["description"] = self.description
        if self.mime_type:
            result["mimeType"] = self.mime_type
        if self.size is not None:
            result["size"] = self.size
        return result


@dataclass
class ResourceTemplate:
    """资源模板"""
    uri_template: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "uriTemplate": self.uri_template,
            "name": self.name,
        }
        if self.description:
            result["description"] = self.description
        if self.mime_type:
            result["mimeType"] = self.mime_type
        return result


@dataclass
class TextResourceContents:
    """文本资源内容"""
    uri: str
    text: str
    mime_type: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "uri": self.uri,
            "text": self.text,
        }
        if self.mime_type:
            result["mimeType"] = self.mime_type
        return result


@dataclass
class BlobResourceContents:
    """二进制资源内容"""
    uri: str
    blob: str
    mime_type: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "uri": self.uri,
            "blob": self.blob,
        }
        if self.mime_type:
            result["mimeType"] = self.mime_type
        return result


@dataclass
class ResourceReadResult:
    """资源读取结果"""
    contents: list[Union[TextResourceContents, BlobResourceContents]]
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "contents": [c.to_dict() for c in self.contents],
        }


class ResourceRegistry:
    """资源注册表"""
    
    def __init__(self):
        self._resources: dict[str, Resource] = {}
        self._templates: dict[str, ResourceTemplate] = {}
        self._handlers: dict[str, Callable] = {}
        self._subscriptions: dict[str, set[str]] = {}
    
    def register(
        self,
        uri: str,
        name: str,
        description: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Callable:
        """
        注册资源装饰器
        
        Args:
            uri: 资源 URI
            name: 资源名称
            description: 资源描述
            mime_type: MIME 类型
        
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            resource = Resource(
                uri=uri,
                name=name,
                description=description,
                mime_type=mime_type,
            )
            self._resources[uri] = resource
            self._handlers[uri] = func
            return func
        
        return decorator
    
    def register_resource(self, resource: Resource, handler: Callable):
        """
        直接注册资源
        
        Args:
            resource: 资源对象
            handler: 处理函数
        """
        self._resources[resource.uri] = resource
        self._handlers[resource.uri] = handler
    
    def register_template(
        self,
        uri_template: str,
        name: str,
        description: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Callable:
        """
        注册资源模板装饰器
        
        Args:
            uri_template: URI 模板
            name: 资源名称
            description: 资源描述
            mime_type: MIME 类型
        
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            template = ResourceTemplate(
                uri_template=uri_template,
                name=name,
                description=description,
                mime_type=mime_type,
            )
            self._templates[uri_template] = template
            self._handlers[uri_template] = func
            return func
        
        return decorator
    
    def get_resource(self, uri: str) -> Optional[Resource]:
        """
        获取资源
        
        Args:
            uri: 资源 URI
        
        Returns:
            资源对象或 None
        """
        return self._resources.get(uri)
    
    def list_resources(self, cursor: Optional[str] = None) -> tuple[list[Resource], Optional[str]]:
        """
        列出资源
        
        Args:
            cursor: 分页游标
        
        Returns:
            (资源列表, 下一页游标)
        """
        return list(self._resources.values()), None
    
    def list_templates(self, cursor: Optional[str] = None) -> tuple[list[ResourceTemplate], Optional[str]]:
        """
        列出资源模板
        
        Args:
            cursor: 分页游标
        
        Returns:
            (资源模板列表, 下一页游标)
        """
        return list(self._templates.values()), None
    
    def has_resources(self) -> bool:
        """检查是否有资源"""
        return len(self._resources) > 0 or len(self._templates) > 0
    
    async def read_resource(self, uri: str) -> ResourceReadResult:
        """
        读取资源
        
        Args:
            uri: 资源 URI
        
        Returns:
            资源读取结果
        """
        if uri in self._handlers:
            handler = self._handlers[uri]
            result = handler()
            
            import inspect
            if inspect.isawaitable(result):
                result = await result
            
            if isinstance(result, ResourceReadResult):
                return result
            elif isinstance(result, str):
                return ResourceReadResult(
                    contents=[TextResourceContents(uri=uri, text=result)]
                )
            elif isinstance(result, bytes):
                import base64
                return ResourceReadResult(
                    contents=[BlobResourceContents(
                        uri=uri,
                        blob=base64.b64encode(result).decode('utf-8')
                    )]
                )
            else:
                return ResourceReadResult(
                    contents=[TextResourceContents(uri=uri, text=str(result))]
                )
        
        for template_uri, handler in self._handlers.items():
            if template_uri in self._templates:
                import re
                pattern = template_uri.replace("{", "(?P<").replace("}", ">[^/]+)")
                match = re.match(pattern, uri)
                if match:
                    result = handler(**match.groupdict())
                    
                    import inspect
                    if inspect.isawaitable(result):
                        result = await result
                    
                    if isinstance(result, ResourceReadResult):
                        return result
                    elif isinstance(result, str):
                        return ResourceReadResult(
                            contents=[TextResourceContents(uri=uri, text=result)]
                        )
                    else:
                        return ResourceReadResult(
                            contents=[TextResourceContents(uri=uri, text=str(result))]
                        )
        
        raise ValueError(f"Resource not found: {uri}")
    
    def subscribe(self, uri: str, client_id: str):
        """
        订阅资源更新
        
        Args:
            uri: 资源 URI
            client_id: 客户端 ID
        """
        if uri not in self._subscriptions:
            self._subscriptions[uri] = set()
        self._subscriptions[uri].add(client_id)
    
    def unsubscribe(self, uri: str, client_id: str):
        """
        取消订阅资源更新
        
        Args:
            uri: 资源 URI
            client_id: 客户端 ID
        """
        if uri in self._subscriptions:
            self._subscriptions[uri].discard(client_id)
            if not self._subscriptions[uri]:
                del self._subscriptions[uri]
    
    def get_subscribers(self, uri: str) -> set[str]:
        """
        获取资源订阅者
        
        Args:
            uri: 资源 URI
        
        Returns:
            订阅者集合
        """
        return self._subscriptions.get(uri, set())
    
    def create_list_response(self, cursor: Optional[str] = None) -> dict:
        """
        创建资源列表响应
        
        Args:
            cursor: 分页游标
        
        Returns:
            响应字典
        """
        resources, next_cursor = self.list_resources(cursor)
        result = {
            "resources": [r.to_dict() for r in resources],
        }
        if next_cursor:
            result["nextCursor"] = next_cursor
        return result
    
    def create_templates_list_response(self, cursor: Optional[str] = None) -> dict:
        """
        创建资源模板列表响应
        
        Args:
            cursor: 分页游标
        
        Returns:
            响应字典
        """
        templates, next_cursor = self.list_templates(cursor)
        result = {
            "resourceTemplates": [t.to_dict() for t in templates],
        }
        if next_cursor:
            result["nextCursor"] = next_cursor
        return result


class BaseResource(ABC):
    """资源基类"""
    
    @property
    @abstractmethod
    def uri(self) -> str:
        """资源 URI"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """资源名称"""
        pass
    
    @property
    def description(self) -> Optional[str]:
        """资源描述"""
        return None
    
    @property
    def mime_type(self) -> Optional[str]:
        """MIME 类型"""
        return None
    
    @abstractmethod
    async def read(self) -> Union[str, bytes, ResourceReadResult]:
        """读取资源"""
        pass
    
    def to_resource(self) -> Resource:
        """转换为资源对象"""
        return Resource(
            uri=self.uri,
            name=self.name,
            description=self.description,
            mime_type=self.mime_type,
        )

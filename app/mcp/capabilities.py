"""
MCP 能力协商模块

实现服务器和客户端能力声明与协商。
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ClientCapabilities:
    """客户端能力"""
    roots: Optional[dict] = None
    sampling: Optional[dict] = None
    experimental: Optional[dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {}
        if self.roots is not None:
            result["roots"] = self.roots
        if self.sampling is not None:
            result["sampling"] = self.sampling
        if self.experimental is not None:
            result["experimental"] = self.experimental
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "ClientCapabilities":
        """从字典创建客户端能力"""
        return cls(
            roots=data.get("roots"),
            sampling=data.get("sampling"),
            experimental=data.get("experimental"),
        )


@dataclass
class ServerCapabilities:
    """服务器能力"""
    prompts: Optional[dict] = None
    resources: Optional[dict] = None
    tools: Optional[dict] = None
    logging: Optional[dict] = None
    completions: Optional[dict] = None
    experimental: Optional[dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {}
        if self.prompts is not None:
            result["prompts"] = self.prompts
        if self.resources is not None:
            result["resources"] = self.resources
        if self.tools is not None:
            result["tools"] = self.tools
        if self.logging is not None:
            result["logging"] = self.logging
        if self.completions is not None:
            result["completions"] = self.completions
        if self.experimental is not None:
            result["experimental"] = self.experimental
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "ServerCapabilities":
        """从字典创建服务器能力"""
        return cls(
            prompts=data.get("prompts"),
            resources=data.get("resources"),
            tools=data.get("tools"),
            logging=data.get("logging"),
            completions=data.get("completions"),
            experimental=data.get("experimental"),
        )


@dataclass
class ImplementationInfo:
    """实现信息"""
    name: str
    version: str
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "name": self.name,
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ImplementationInfo":
        """从字典创建实现信息"""
        return cls(
            name=data["name"],
            version=data["version"],
        )


@dataclass
class InitializeParams:
    """初始化请求参数"""
    protocol_version: str
    capabilities: ClientCapabilities
    client_info: ImplementationInfo
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "protocolVersion": self.protocol_version,
            "capabilities": self.capabilities.to_dict(),
            "clientInfo": self.client_info.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "InitializeParams":
        """从字典创建初始化参数"""
        return cls(
            protocol_version=data["protocolVersion"],
            capabilities=ClientCapabilities.from_dict(data.get("capabilities", {})),
            client_info=ImplementationInfo.from_dict(data["clientInfo"]),
        )


@dataclass
class InitializeResult:
    """初始化响应结果"""
    protocol_version: str
    capabilities: ServerCapabilities
    server_info: ImplementationInfo
    instructions: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "protocolVersion": self.protocol_version,
            "capabilities": self.capabilities.to_dict(),
            "serverInfo": self.server_info.to_dict(),
        }
        if self.instructions is not None:
            result["instructions"] = self.instructions
        return result


class CapabilityNegotiator:
    """能力协商器"""
    
    PROTOCOL_VERSION = "2025-03-26"
    
    def __init__(
        self,
        server_name: str = "OpenCrawler MCP Server",
        server_version: str = "1.0.0",
        instructions: Optional[str] = None,
    ):
        self.server_name = server_name
        self.server_version = server_version
        self.instructions = instructions or self._get_default_instructions()
        
        self._client_capabilities: Optional[ClientCapabilities] = None
        self._client_info: Optional[ImplementationInfo] = None
        self._initialized = False
        
        self._prompts_enabled = False
        self._resources_enabled = False
        self._tools_enabled = False
        self._logging_enabled = False
        self._completions_enabled = False
        
        self._prompts_list_changed = False
        self._resources_subscribe = False
        self._resources_list_changed = False
        self._tools_list_changed = False
    
    def _get_default_instructions(self) -> str:
        """获取默认使用说明"""
        return """OpenCrawler MCP Server - 网页内容提取工具

本服务器提供以下功能：
- crawl_webpage: 抓取网页并转换为 Markdown
- extract_content: 提取网页内容
- get_page_title: 获取网页标题
- save_article: 保存文章为 Markdown 文件
- list_platforms: 列出支持的平台

使用时请提供有效的 URL，服务器将自动检测平台并提取内容。"""
    
    def enable_prompts(self, list_changed: bool = True):
        """启用 Prompts 功能"""
        self._prompts_enabled = True
        self._prompts_list_changed = list_changed
    
    def enable_resources(self, subscribe: bool = False, list_changed: bool = True):
        """启用 Resources 功能"""
        self._resources_enabled = True
        self._resources_subscribe = subscribe
        self._resources_list_changed = list_changed
    
    def enable_tools(self, list_changed: bool = True):
        """启用 Tools 功能"""
        self._tools_enabled = True
        self._tools_list_changed = list_changed
    
    def enable_logging(self):
        """启用 Logging 功能"""
        self._logging_enabled = True
    
    def enable_completions(self):
        """启用 Completions 功能"""
        self._completions_enabled = True
    
    def get_server_capabilities(self) -> ServerCapabilities:
        """获取服务器能力"""
        capabilities = ServerCapabilities()
        
        if self._prompts_enabled:
            capabilities.prompts = {}
            if self._prompts_list_changed:
                capabilities.prompts["listChanged"] = True
        
        if self._resources_enabled:
            capabilities.resources = {}
            if self._resources_subscribe:
                capabilities.resources["subscribe"] = True
            if self._resources_list_changed:
                capabilities.resources["listChanged"] = True
        
        if self._tools_enabled:
            capabilities.tools = {}
            if self._tools_list_changed:
                capabilities.tools["listChanged"] = True
        
        if self._logging_enabled:
            capabilities.logging = {}
        
        if self._completions_enabled:
            capabilities.completions = {}
        
        return capabilities
    
    def negotiate(self, params: InitializeParams) -> InitializeResult:
        """
        执行能力协商
        
        Args:
            params: 初始化参数
        
        Returns:
            初始化结果
        """
        self._client_capabilities = params.capabilities
        self._client_info = params.client_info
        
        protocol_version = params.protocol_version
        if protocol_version != self.PROTOCOL_VERSION:
            pass
        
        return InitializeResult(
            protocol_version=self.PROTOCOL_VERSION,
            capabilities=self.get_server_capabilities(),
            server_info=ImplementationInfo(
                name=self.server_name,
                version=self.server_version,
            ),
            instructions=self.instructions,
        )
    
    def set_initialized(self):
        """标记初始化完成"""
        self._initialized = True
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    def get_client_capabilities(self) -> Optional[ClientCapabilities]:
        """获取客户端能力"""
        return self._client_capabilities
    
    def get_client_info(self) -> Optional[ImplementationInfo]:
        """获取客户端信息"""
        return self._client_info
    
    def has_roots_capability(self) -> bool:
        """检查客户端是否有 roots 能力"""
        return self._client_capabilities is not None and self._client_capabilities.roots is not None
    
    def has_sampling_capability(self) -> bool:
        """检查客户端是否有 sampling 能力"""
        return self._client_capabilities is not None and self._client_capabilities.sampling is not None

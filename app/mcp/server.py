"""
MCP Server 主类

实现完整的 MCP 服务器，整合协议处理、传输层、能力协商和功能模块。
"""

import asyncio
import logging
from typing import Any, Optional, Union

from app.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    JSONRPCErrorCodes,
    JSONRPCMessageParser,
)
from app.mcp.transport import BaseTransport, StdioTransport, TransportFactory
from app.mcp.capabilities import (
    CapabilityNegotiator,
    InitializeParams,
    InitializeResult,
)
from app.mcp.tools import ToolRegistry, ToolResult
from app.mcp.resources import ResourceRegistry
from app.mcp.prompts import PromptRegistry


logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP 服务器
    
    实现完整的 MCP 协议服务器，支持：
    - 协议握手和能力协商
    - Tools 工具调用
    - Resources 资源访问
    - Prompts 提示模板
    """
    
    def __init__(
        self,
        name: str = "OpenCrawler MCP Server",
        version: str = "1.0.0",
        instructions: Optional[str] = None,
    ):
        """
        初始化 MCP 服务器
        
        Args:
            name: 服务器名称
            version: 服务器版本
            instructions: 使用说明
        """
        self._name = name
        self._version = version
        
        self._negotiator = CapabilityNegotiator(
            server_name=name,
            server_version=version,
            instructions=instructions,
        )
        
        self._tools = ToolRegistry()
        self._resources = ResourceRegistry()
        self._prompts = PromptRegistry()
        
        self._transport: Optional[BaseTransport] = None
        self._running = False
        
        self._request_handlers: dict[str, callable] = {}
        self._notification_handlers: dict[str, callable] = {}
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置内置请求处理器"""
        self._request_handlers = {
            "initialize": self._handle_initialize,
            "ping": self._handle_ping,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/templates/list": self._handle_resources_templates_list,
            "resources/read": self._handle_resources_read,
            "resources/subscribe": self._handle_resources_subscribe,
            "resources/unsubscribe": self._handle_resources_unsubscribe,
            "prompts/list": self._handle_prompts_list,
            "prompts/get": self._handle_prompts_get,
            "logging/setLevel": self._handle_logging_set_level,
        }
        
        self._notification_handlers = {
            "notifications/initialized": self._handle_initialized,
            "notifications/cancelled": self._handle_cancelled,
        }
    
    @property
    def tools(self) -> ToolRegistry:
        """获取工具注册表"""
        return self._tools
    
    @property
    def resources(self) -> ResourceRegistry:
        """获取资源注册表"""
        return self._resources
    
    @property
    def prompts(self) -> PromptRegistry:
        """获取提示注册表"""
        return self._prompts
    
    def enable_tools(self, list_changed: bool = True):
        """启用工具功能"""
        self._negotiator.enable_tools(list_changed)
    
    def enable_resources(self, subscribe: bool = False, list_changed: bool = True):
        """启用资源功能"""
        self._negotiator.enable_resources(subscribe, list_changed)
    
    def enable_prompts(self, list_changed: bool = True):
        """启用提示功能"""
        self._negotiator.enable_prompts(list_changed)
    
    def enable_logging(self):
        """启用日志功能"""
        self._negotiator.enable_logging()
    
    async def _handle_initialize(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理初始化请求"""
        try:
            params = InitializeParams.from_dict(request.params or {})
            result = self._negotiator.negotiate(params)
            
            return JSONRPCResponse.create_success(
                request_id=request.id,
                result=result.to_dict(),
            )
        except Exception as e:
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_PARAMS.value,
                message=str(e),
            )
    
    async def _handle_ping(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理 ping 请求"""
        return JSONRPCResponse.create_success(
            request_id=request.id,
            result={},
        )
    
    async def _handle_tools_list(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理工具列表请求"""
        if not self._negotiator.is_initialized():
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_REQUEST.value,
                message="Server not initialized",
            )
        
        cursor = request.params.get("cursor") if request.params else None
        result = self._tools.create_list_response(cursor)
        
        return JSONRPCResponse.create_success(
            request_id=request.id,
            result=result,
        )
    
    async def _handle_tools_call(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理工具调用请求"""
        if not self._negotiator.is_initialized():
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_REQUEST.value,
                message="Server not initialized",
            )
        
        params = request.params or {}
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_PARAMS.value,
                message="Missing tool name",
            )
        
        result = await self._tools.call_tool(name, arguments)
        
        return JSONRPCResponse.create_success(
            request_id=request.id,
            result=result.to_dict(),
        )
    
    async def _handle_resources_list(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理资源列表请求"""
        if not self._negotiator.is_initialized():
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_REQUEST.value,
                message="Server not initialized",
            )
        
        cursor = request.params.get("cursor") if request.params else None
        result = self._resources.create_list_response(cursor)
        
        return JSONRPCResponse.create_success(
            request_id=request.id,
            result=result,
        )
    
    async def _handle_resources_templates_list(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理资源模板列表请求"""
        if not self._negotiator.is_initialized():
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_REQUEST.value,
                message="Server not initialized",
            )
        
        cursor = request.params.get("cursor") if request.params else None
        result = self._resources.create_templates_list_response(cursor)
        
        return JSONRPCResponse.create_success(
            request_id=request.id,
            result=result,
        )
    
    async def _handle_resources_read(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理资源读取请求"""
        if not self._negotiator.is_initialized():
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_REQUEST.value,
                message="Server not initialized",
            )
        
        params = request.params or {}
        uri = params.get("uri")
        
        if not uri:
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_PARAMS.value,
                message="Missing resource URI",
            )
        
        try:
            result = await self._resources.read_resource(uri)
            return JSONRPCResponse.create_success(
                request_id=request.id,
                result=result.to_dict(),
            )
        except ValueError as e:
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.MCP_RESOURCE_NOT_FOUND.value,
                message=str(e),
            )
        except Exception as e:
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.MCP_RESOURCE_READ_ERROR.value,
                message=f"Failed to read resource: {e}",
            )
    
    async def _handle_resources_subscribe(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理资源订阅请求"""
        if not self._negotiator.is_initialized():
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_REQUEST.value,
                message="Server not initialized",
            )
        
        params = request.params or {}
        uri = params.get("uri")
        
        if not uri:
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_PARAMS.value,
                message="Missing resource URI",
            )
        
        client_id = str(request.id)
        self._resources.subscribe(uri, client_id)
        
        return JSONRPCResponse.create_success(
            request_id=request.id,
            result={},
        )
    
    async def _handle_resources_unsubscribe(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理资源取消订阅请求"""
        params = request.params or {}
        uri = params.get("uri")
        
        if not uri:
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_PARAMS.value,
                message="Missing resource URI",
            )
        
        client_id = str(request.id)
        self._resources.unsubscribe(uri, client_id)
        
        return JSONRPCResponse.create_success(
            request_id=request.id,
            result={},
        )
    
    async def _handle_prompts_list(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理提示列表请求"""
        if not self._negotiator.is_initialized():
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_REQUEST.value,
                message="Server not initialized",
            )
        
        cursor = request.params.get("cursor") if request.params else None
        result = self._prompts.create_list_response(cursor)
        
        return JSONRPCResponse.create_success(
            request_id=request.id,
            result=result,
        )
    
    async def _handle_prompts_get(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理提示获取请求"""
        if not self._negotiator.is_initialized():
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_REQUEST.value,
                message="Server not initialized",
            )
        
        params = request.params or {}
        name = params.get("name")
        arguments = params.get("arguments")
        
        if not name:
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_PARAMS.value,
                message="Missing prompt name",
            )
        
        try:
            result = await self._prompts.get_prompt_result(name, arguments)
            return JSONRPCResponse.create_success(
                request_id=request.id,
                result=result.to_dict(),
            )
        except ValueError as e:
            return JSONRPCResponse.create_error(
                request_id=request.id,
                code=JSONRPCErrorCodes.INVALID_PARAMS.value,
                message=str(e),
            )
    
    async def _handle_logging_set_level(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理日志级别设置请求"""
        params = request.params or {}
        level = params.get("level", "info")
        
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "notice": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
            "alert": logging.CRITICAL,
            "emergency": logging.CRITICAL,
        }
        
        if level.lower() in level_map:
            logging.getLogger().setLevel(level_map[level.lower()])
        
        return JSONRPCResponse.create_success(
            request_id=request.id,
            result={},
        )
    
    async def _handle_initialized(self, notification: JSONRPCNotification):
        """处理初始化完成通知"""
        self._negotiator.set_initialized()
    
    async def _handle_cancelled(self, notification: JSONRPCNotification):
        """处理取消通知"""
        pass
    
    async def _process_message(
        self,
        message: Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification],
    ) -> Optional[JSONRPCResponse]:
        """
        处理消息
        
        Args:
            message: 接收到的消息
        
        Returns:
            响应消息（如果需要）
        """
        if isinstance(message, JSONRPCRequest):
            handler = self._request_handlers.get(message.method)
            if handler:
                return await handler(message)
            else:
                return JSONRPCResponse.create_error(
                    request_id=message.id,
                    code=JSONRPCErrorCodes.METHOD_NOT_FOUND.value,
                    message=f"Method not found: {message.method}",
                )
        
        elif isinstance(message, JSONRPCNotification):
            handler = self._notification_handlers.get(message.method)
            if handler:
                await handler(message)
            return None
        
        return None
    
    async def _message_handler(self, message: Any):
        """传输层消息处理器"""
        if isinstance(message, list):
            for msg in message:
                response = await self._process_message(msg)
                if response and self._transport:
                    await self._transport.send(response)
        else:
            response = await self._process_message(message)
            if response and self._transport:
                await self._transport.send(response)
    
    async def start_stdio(self):
        """启动 stdio 传输"""
        self._transport = TransportFactory.create_stdio()
        self._transport.set_message_handler(self._message_handler)
        
        self._running = True
        await self._transport.start()
        
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()
    
    async def stop(self):
        """停止服务器"""
        self._running = False
        if self._transport:
            await self._transport.stop()
            self._transport = None
    
    def register_request_handler(self, method: str, handler: callable):
        """
        注册自定义请求处理器
        
        Args:
            method: 方法名
            handler: 处理函数
        """
        self._request_handlers[method] = handler
    
    def register_notification_handler(self, method: str, handler: callable):
        """
        注册自定义通知处理器
        
        Args:
            method: 方法名
            handler: 处理函数
        """
        self._notification_handlers[method] = handler
    
    async def send_notification(self, notification: JSONRPCNotification):
        """
        发送通知
        
        Args:
            notification: 通知对象
        """
        if self._transport:
            await self._transport.send(notification)
    
    def create_tools_list_changed_notification(self) -> JSONRPCNotification:
        """创建工具列表变更通知"""
        return JSONRPCNotification(
            method="notifications/tools/list_changed",
        )
    
    def create_resources_list_changed_notification(self) -> JSONRPCNotification:
        """创建资源列表变更通知"""
        return JSONRPCNotification(
            method="notifications/resources/list_changed",
        )
    
    def create_prompts_list_changed_notification(self) -> JSONRPCNotification:
        """创建提示列表变更通知"""
        return JSONRPCNotification(
            method="notifications/prompts/list_changed",
        )

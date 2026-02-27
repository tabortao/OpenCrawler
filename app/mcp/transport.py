"""
MCP 传输层实现

实现 stdio 和 HTTP 两种传输方式。
"""

import asyncio
import sys
import json
from abc import ABC, abstractmethod
from typing import Callable, Optional, Any
from dataclasses import dataclass

from app.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    JSONRPCMessageParser,
)


class BaseTransport(ABC):
    """传输层基类"""
    
    def __init__(self):
        self._message_handler: Optional[Callable] = None
        self._running = False
    
    @abstractmethod
    async def start(self):
        """启动传输层"""
        pass
    
    @abstractmethod
    async def stop(self):
        """停止传输层"""
        pass
    
    @abstractmethod
    async def send(self, message: JSONRPCResponse | JSONRPCNotification):
        """发送消息"""
        pass
    
    def set_message_handler(self, handler: Callable):
        """
        设置消息处理器
        
        Args:
            handler: 消息处理函数
        """
        self._message_handler = handler


class StdioTransport(BaseTransport):
    """
    stdio 传输层实现
    
    通过标准输入/输出进行通信，适用于本地进程间通信。
    """
    
    def __init__(self, input_stream=None, output_stream=None, error_stream=None):
        super().__init__()
        self._input = input_stream or sys.stdin
        self._output = output_stream or sys.stdout
        self._error = error_stream or sys.stderr
        self._reader: Optional[asyncio.StreamReader] = None
        self._read_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动 stdio 传输层"""
        self._running = True
        
        if hasattr(self._input, 'buffer'):
            loop = asyncio.get_event_loop()
            self._reader = asyncio.StreamReader()
            reader_protocol = asyncio.StreamReaderProtocol(self._reader)
            await loop.connect_read_pipe(lambda: reader_protocol, self._input.buffer)
        
        self._read_task = asyncio.create_task(self._read_loop())
    
    async def stop(self):
        """停止 stdio 传输层"""
        self._running = False
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
    
    async def _read_loop(self):
        """读取输入循环"""
        while self._running:
            try:
                if self._reader:
                    line = await self._reader.readline()
                    if not line:
                        break
                else:
                    line = await asyncio.get_event_loop().run_in_executor(
                        None, self._input.readline
                    )
                    if not line:
                        break
                
                line = line.decode('utf-8') if isinstance(line, bytes) else line
                line = line.strip()
                
                if not line:
                    continue
                
                try:
                    message = JSONRPCMessageParser.parse(line)
                    if self._message_handler:
                        await self._message_handler(message)
                except ValueError as e:
                    await self._log_error(f"Failed to parse message: {e}")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self._log_error(f"Error reading from stdin: {e}")
                break
    
    async def send(self, message: JSONRPCResponse | JSONRPCNotification):
        """
        发送消息到标准输出
        
        Args:
            message: 要发送的消息
        """
        try:
            data = JSONRPCMessageParser.serialize(message)
            if hasattr(self._output, 'buffer'):
                self._output.buffer.write((data + '\n').encode('utf-8'))
                self._output.buffer.flush()
            else:
                self._output.write(data + '\n')
                self._output.flush()
        except Exception as e:
            await self._log_error(f"Error sending message: {e}")
    
    async def _log_error(self, message: str):
        """
        记录错误到标准错误输出
        
        Args:
            message: 错误消息
        """
        error_data = json.dumps({"level": "error", "message": message})
        if hasattr(self._error, 'buffer'):
            self._error.buffer.write((error_data + '\n').encode('utf-8'))
            self._error.buffer.flush()
        else:
            self._error.write(error_data + '\n')
            self._error.flush()


@dataclass
class HTTPTransportConfig:
    """HTTP 传输配置"""
    host: str = "127.0.0.1"
    port: int = 3000
    endpoint: str = "/mcp"
    session_timeout: int = 3600


class HTTPTransport(BaseTransport):
    """
    HTTP 传输层实现
    
    通过 HTTP POST/GET + SSE 进行通信，适用于远程服务。
    """
    
    def __init__(self, config: Optional[HTTPTransportConfig] = None):
        super().__init__()
        self.config = config or HTTPTransportConfig()
        self._sessions: dict[str, Any] = {}
        self._sse_queues: dict[str, asyncio.Queue] = {}
    
    async def start(self):
        """启动 HTTP 传输层"""
        self._running = True
    
    async def stop(self):
        """停止 HTTP 传输层"""
        self._running = False
        self._sessions.clear()
        for queue in self._sse_queues.values():
            while not queue.empty():
                queue.get_nowait()
        self._sse_queues.clear()
    
    async def send(self, message: JSONRPCResponse | JSONRPCNotification, session_id: Optional[str] = None):
        """
        发送消息
        
        Args:
            message: 要发送的消息
            session_id: 会话 ID（可选）
        """
        if session_id and session_id in self._sse_queues:
            await self._sse_queues[session_id].put(message)
    
    async def handle_post(self, body: bytes, session_id: Optional[str] = None) -> tuple[int, str, Optional[str]]:
        """
        处理 HTTP POST 请求
        
        Args:
            body: 请求体
            session_id: 会话 ID
        
        Returns:
            (状态码, 响应体, 新会话 ID)
        """
        try:
            data = body.decode('utf-8')
            message = JSONRPCMessageParser.parse(data)
            
            if self._message_handler:
                response = await self._message_handler(message, session_id)
                if response:
                    if isinstance(response, tuple):
                        response_data, new_session_id = response
                    else:
                        response_data = response
                        new_session_id = None
                    
                    return 200, JSONRPCMessageParser.serialize(response_data), new_session_id
            
            return 202, "", None
            
        except ValueError as e:
            error_response = JSONRPCResponse(
                id="",
                error={"code": -32700, "message": str(e)},
            )
            return 400, JSONRPCMessageParser.serialize(error_response), None
    
    def create_sse_queue(self, session_id: str) -> asyncio.Queue:
        """
        创建 SSE 队列
        
        Args:
            session_id: 会话 ID
        
        Returns:
            消息队列
        """
        queue = asyncio.Queue()
        self._sse_queues[session_id] = queue
        return queue
    
    def remove_sse_queue(self, session_id: str):
        """
        移除 SSE 队列
        
        Args:
            session_id: 会话 ID
        """
        if session_id in self._sse_queues:
            del self._sse_queues[session_id]


class TransportFactory:
    """传输层工厂"""
    
    @staticmethod
    def create_stdio() -> StdioTransport:
        """创建 stdio 传输层"""
        return StdioTransport()
    
    @staticmethod
    def create_http(config: Optional[HTTPTransportConfig] = None) -> HTTPTransport:
        """创建 HTTP 传输层"""
        return HTTPTransport(config)

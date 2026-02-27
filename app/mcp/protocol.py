"""
JSON-RPC 2.0 协议实现

实现 MCP 协议所需的 JSON-RPC 2.0 消息类型和处理逻辑。
"""

import json
from dataclasses import dataclass, field
from typing import Any, Optional, Union
from enum import Enum


class JSONRPCErrorCodes(Enum):
    """JSON-RPC 标准错误码"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    MCP_RESOURCE_NOT_FOUND = -32002
    MCP_RESOURCE_READ_ERROR = -32003


@dataclass
class JSONRPCError:
    """JSON-RPC 错误对象"""
    code: int
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.data is not None:
            result["data"] = self.data
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "JSONRPCError":
        """从字典创建错误对象"""
        return cls(
            code=data["code"],
            message=data["message"],
            data=data.get("data"),
        )


@dataclass
class JSONRPCRequest:
    """JSON-RPC 请求对象"""
    id: Union[str, int]
    method: str
    params: Optional[dict[str, Any]] = None
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "method": self.method,
        }
        if self.params is not None:
            result["params"] = self.params
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "JSONRPCRequest":
        """从字典创建请求对象"""
        if "id" not in data:
            raise ValueError("Request must have an 'id' field")
        if "method" not in data:
            raise ValueError("Request must have a 'method' field")
        
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data["id"],
            method=data["method"],
            params=data.get("params"),
        )


@dataclass
class JSONRPCResponse:
    """JSON-RPC 响应对象"""
    id: Union[str, int]
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
        }
        if self.error is not None:
            result["error"] = self.error.to_dict()
        else:
            result["result"] = self.result
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "JSONRPCResponse":
        """从字典创建响应对象"""
        error = None
        if "error" in data:
            error = JSONRPCError.from_dict(data["error"])
        
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data["id"],
            result=data.get("result"),
            error=error,
        )
    
    @classmethod
    def create_success(cls, request_id: Union[str, int], result: Any) -> "JSONRPCResponse":
        """创建成功响应"""
        return cls(id=request_id, result=result)
    
    @classmethod
    def create_error(
        cls,
        request_id: Union[str, int],
        code: int,
        message: str,
        data: Optional[Any] = None,
    ) -> "JSONRPCResponse":
        """创建错误响应"""
        return cls(
            id=request_id,
            error=JSONRPCError(code=code, message=message, data=data),
        )


@dataclass
class JSONRPCNotification:
    """JSON-RPC 通知对象"""
    method: str
    params: Optional[dict[str, Any]] = None
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
        }
        if self.params is not None:
            result["params"] = self.params
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "JSONRPCNotification":
        """从字典创建通知对象"""
        if "method" not in data:
            raise ValueError("Notification must have a 'method' field")
        
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data["method"],
            params=data.get("params"),
        )


class JSONRPCMessageParser:
    """JSON-RPC 消息解析器"""
    
    @staticmethod
    def parse(data: str) -> Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification, list]:
        """
        解析 JSON-RPC 消息
        
        Args:
            data: JSON 字符串
        
        Returns:
            解析后的消息对象或消息列表
        """
        try:
            obj = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        
        if isinstance(obj, list):
            return [JSONRPCMessageParser._parse_single(item) for item in obj]
        
        return JSONRPCMessageParser._parse_single(obj)
    
    @staticmethod
    def _parse_single(obj: dict) -> Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]:
        """解析单个消息对象"""
        if obj.get("jsonrpc") != "2.0":
            raise ValueError("Invalid JSON-RPC version")
        
        if "id" in obj:
            if "method" in obj:
                return JSONRPCRequest.from_dict(obj)
            elif "result" in obj or "error" in obj:
                return JSONRPCResponse.from_dict(obj)
            else:
                raise ValueError("Invalid message: must have 'method' or 'result'/'error'")
        else:
            if "method" in obj:
                return JSONRPCNotification.from_dict(obj)
            else:
                raise ValueError("Invalid notification: must have 'method'")
    
    @staticmethod
    def serialize(message: Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification, list]) -> str:
        """
        序列化消息为 JSON 字符串
        
        Args:
            message: 消息对象或消息列表
        
        Returns:
            JSON 字符串
        """
        if isinstance(message, list):
            return json.dumps([m.to_dict() for m in message])
        return json.dumps(message.to_dict())


class ProgressToken:
    """进度令牌，用于跟踪长时间运行的操作"""
    
    def __init__(self, token: Union[str, int]):
        self.token = token
    
    def create_progress_notification(self, progress: float, total: Optional[float] = None) -> JSONRPCNotification:
        """
        创建进度通知
        
        Args:
            progress: 当前进度
            total: 总进度（可选）
        
        Returns:
            进度通知对象
        """
        params = {
            "progressToken": self.token,
            "progress": progress,
        }
        if total is not None:
            params["total"] = total
        
        return JSONRPCNotification(
            method="notifications/progress",
            params=params,
        )

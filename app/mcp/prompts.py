"""
MCP Prompts 模块

实现 MCP 提示模板注册和获取功能。
"""

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union
from abc import ABC, abstractmethod


@dataclass
class PromptArgument:
    """提示参数"""
    name: str
    description: Optional[str] = None
    required: bool = False
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "name": self.name,
        }
        if self.description:
            result["description"] = self.description
        if self.required:
            result["required"] = self.required
        return result


@dataclass
class Prompt:
    """提示定义"""
    name: str
    description: Optional[str] = None
    arguments: list[PromptArgument] = field(default_factory=list)
    handler: Optional[Callable] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "name": self.name,
        }
        if self.description:
            result["description"] = self.description
        if self.arguments:
            result["arguments"] = [a.to_dict() for a in self.arguments]
        return result


@dataclass
class TextPromptContent:
    """文本提示内容"""
    type: str = "text"
    text: str = ""
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "type": self.type,
            "text": self.text,
        }


@dataclass
class ImagePromptContent:
    """图片提示内容"""
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
class ResourcePromptContent:
    """资源提示内容"""
    type: str = "resource"
    resource: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "type": self.type,
            "resource": self.resource,
        }


@dataclass
class PromptMessage:
    """提示消息"""
    role: str
    content: Union[TextPromptContent, ImagePromptContent, ResourcePromptContent]
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "role": self.role,
            "content": self.content.to_dict(),
        }


@dataclass
class PromptResult:
    """提示获取结果"""
    description: Optional[str] = None
    messages: list[PromptMessage] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {}
        if self.description:
            result["description"] = self.description
        result["messages"] = [m.to_dict() for m in self.messages]
        return result
    
    @classmethod
    def user_message(cls, text: str, description: Optional[str] = None) -> "PromptResult":
        """创建用户消息结果"""
        return cls(
            description=description,
            messages=[PromptMessage(
                role="user",
                content=TextPromptContent(text=text),
            )],
        )
    
    @classmethod
    def assistant_message(cls, text: str, description: Optional[str] = None) -> "PromptResult":
        """创建助手消息结果"""
        return cls(
            description=description,
            messages=[PromptMessage(
                role="assistant",
                content=TextPromptContent(text=text),
            )],
        )
    
    @classmethod
    def conversation(
        cls,
        messages: list[tuple[str, str]],
        description: Optional[str] = None,
    ) -> "PromptResult":
        """
        创建对话结果
        
        Args:
            messages: 消息列表 [(role, text), ...]
            description: 描述
        
        Returns:
            提示结果
        """
        prompt_messages = []
        for role, text in messages:
            prompt_messages.append(PromptMessage(
                role=role,
                content=TextPromptContent(text=text),
            ))
        return cls(description=description, messages=prompt_messages)


class PromptRegistry:
    """提示注册表"""
    
    def __init__(self):
        self._prompts: dict[str, Prompt] = {}
    
    def register(
        self,
        name: str,
        description: Optional[str] = None,
        arguments: Optional[list[PromptArgument]] = None,
    ) -> Callable:
        """
        注册提示装饰器
        
        Args:
            name: 提示名称
            description: 提示描述
            arguments: 提示参数
        
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            args = arguments or self._infer_arguments(func)
            
            prompt = Prompt(
                name=name,
                description=description,
                arguments=args,
                handler=func,
            )
            self._prompts[name] = prompt
            return func
        
        return decorator
    
    def register_prompt(self, prompt: Prompt, handler: Callable):
        """
        直接注册提示
        
        Args:
            prompt: 提示对象
            handler: 处理函数
        """
        prompt.handler = handler
        self._prompts[prompt.name] = prompt
    
    def _infer_arguments(self, func: Callable) -> list[PromptArgument]:
        """从函数签名推断参数"""
        sig = inspect.signature(func)
        arguments = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'cls'):
                continue
            
            arg = PromptArgument(
                name=param_name,
                required=param.default == inspect.Parameter.empty,
            )
            arguments.append(arg)
        
        return arguments
    
    def get_prompt(self, name: str) -> Optional[Prompt]:
        """
        获取提示
        
        Args:
            name: 提示名称
        
        Returns:
            提示对象或 None
        """
        return self._prompts.get(name)
    
    def list_prompts(self, cursor: Optional[str] = None) -> tuple[list[Prompt], Optional[str]]:
        """
        列出提示
        
        Args:
            cursor: 分页游标
        
        Returns:
            (提示列表, 下一页游标)
        """
        return list(self._prompts.values()), None
    
    def has_prompts(self) -> bool:
        """检查是否有提示"""
        return len(self._prompts) > 0
    
    async def get_prompt_result(self, name: str, arguments: Optional[dict] = None) -> PromptResult:
        """
        获取提示结果
        
        Args:
            name: 提示名称
            arguments: 提示参数
        
        Returns:
            提示结果
        """
        prompt = self.get_prompt(name)
        if not prompt:
            raise ValueError(f"Unknown prompt: {name}")
        
        if prompt.handler:
            result = prompt.handler(**(arguments or {}))
            
            if inspect.isawaitable(result):
                result = await result
            
            if isinstance(result, PromptResult):
                return result
            elif isinstance(result, str):
                return PromptResult.user_message(result)
            elif isinstance(result, list):
                return PromptResult.conversation(result)
            else:
                return PromptResult.user_message(str(result))
        
        return PromptResult.user_message(f"Prompt: {name}")
    
    def create_list_response(self, cursor: Optional[str] = None) -> dict:
        """
        创建提示列表响应
        
        Args:
            cursor: 分页游标
        
        Returns:
            响应字典
        """
        prompts, next_cursor = self.list_prompts(cursor)
        result = {
            "prompts": [p.to_dict() for p in prompts],
        }
        if next_cursor:
            result["nextCursor"] = next_cursor
        return result


class BasePrompt(ABC):
    """提示基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """提示名称"""
        pass
    
    @property
    def description(self) -> Optional[str]:
        """提示描述"""
        return None
    
    @property
    def arguments(self) -> list[PromptArgument]:
        """提示参数"""
        return []
    
    @abstractmethod
    async def render(self, **kwargs) -> PromptResult:
        """渲染提示"""
        pass
    
    def to_prompt(self) -> Prompt:
        """转换为提示对象"""
        return Prompt(
            name=self.name,
            description=self.description,
            arguments=self.arguments,
            handler=self.render,
        )

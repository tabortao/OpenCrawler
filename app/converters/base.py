"""
转换器基类模块

定义转换器的抽象基类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ConversionResult:
    """转换结果数据类"""
    
    content: str
    metadata: dict[str, Any]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "metadata": self.metadata,
        }


class BaseConverter(ABC):
    """
    转换器抽象基类
    
    所有转换器都需要继承此类
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """转换器名称"""
        pass
    
    @abstractmethod
    def convert(self, content: str, **kwargs) -> ConversionResult:
        """
        转换内容
        
        Args:
            content: 原始内容
            **kwargs: 额外参数
        
        Returns:
            转换结果
        """
        pass

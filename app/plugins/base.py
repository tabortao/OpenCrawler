"""
插件基类模块

定义插件的抽象基类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from app.crawlers.base import CrawlResult


@dataclass
class PluginInfo:
    """插件信息数据类"""
    
    name: str
    version: str
    description: str
    author: str = ""
    platforms: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


class BasePlugin(ABC):
    """
    插件抽象基类
    
    所有平台插件都需要继承此类
    """
    
    def __init__(self):
        self._enabled = True
    
    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """插件信息"""
        pass
    
    @property
    @abstractmethod
    def platforms(self) -> list[str]:
        """支持的平台列表"""
        pass
    
    @property
    def name(self) -> str:
        """插件名称"""
        return self.info.name
    
    @property
    def enabled(self) -> bool:
        """插件是否启用"""
        return self._enabled
    
    def enable(self):
        """启用插件"""
        self._enabled = True
    
    def disable(self):
        """禁用插件"""
        self._enabled = False
    
    @abstractmethod
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """
        提取页面内容
        
        Args:
            url: 目标 URL
            **kwargs: 额外参数
        
        Returns:
            爬取结果
        """
        pass
    
    def get_content_selector(self) -> str:
        """
        获取内容选择器
        
        Returns:
            CSS 选择器
        """
        return ""
    
    def get_supported_url_patterns(self) -> list[str]:
        """
        获取支持的 URL 模式
        
        Returns:
            URL 正则模式列表
        """
        return []
    
    def can_handle(self, url: str) -> bool:
        """
        检查是否可以处理该 URL
        
        Args:
            url: 目标 URL
        
        Returns:
            是否可以处理
        """
        import re
        
        patterns = self.get_supported_url_patterns()
        if not patterns:
            return False
        
        for pattern in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False
    
    async def on_load(self):
        """插件加载时的回调"""
        pass
    
    async def on_unload(self):
        """插件卸载时的回调"""
        pass
    
    async def on_error(self, url: str, error: Exception):
        """
        发生错误时的回调
        
        Args:
            url: 目标 URL
            error: 异常对象
        """
        print(f"[{self.name}] Error extracting {url}: {error}")

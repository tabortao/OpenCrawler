"""
爬虫基类模块

定义爬虫的抽象基类和通用方法
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from app.core.config import settings
from app.core.exceptions import ContentExtractionError, TimeoutError


@dataclass
class CrawlResult:
    """爬取结果数据类"""
    
    title: str
    url: str
    markdown: str
    html: str = ""
    image_urls: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "url": self.url,
            "markdown": self.markdown,
            "html": self.html,
            "image_urls": self.image_urls,
            "metadata": self.metadata,
        }


class BaseCrawler(ABC):
    """
    爬虫抽象基类
    
    所有平台爬虫都需要继承此类并实现 extract 方法
    """
    
    def __init__(self):
        self.settings = settings
        self._playwright = None
        self._browser = None
        self._context = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """爬虫名称"""
        pass
    
    @property
    @abstractmethod
    def platforms(self) -> list[str]:
        """支持的平台列表"""
        pass
    
    @abstractmethod
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """
        提取页面内容
        
        Args:
            url: 目标 URL
            **kwargs: 额外参数
        
        Returns:
            爬取结果
        
        Raises:
            ContentExtractionError: 内容提取失败
            AuthenticationError: 需要认证
            TimeoutError: 请求超时
        """
        pass
    
    def get_platform_config(self, platform: str):
        """获取平台配置"""
        return self.settings.get_platform_config(platform)
    
    def get_browser_args(self) -> dict:
        """获取浏览器启动参数"""
        return self.settings.get_browser_args()
    
    async def close(self):
        """关闭浏览器资源"""
        try:
            if self._context:
                await self._context.close()
                self._context = None
        except Exception:
            pass
        
        try:
            if self._browser:
                await self._browser.close()
                self._browser = None
        except Exception:
            pass
        
        try:
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
        except Exception:
            pass
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

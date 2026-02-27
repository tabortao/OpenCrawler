"""
爬虫工厂模块

提供爬虫实例的创建和管理，支持自动选择特定插件或通用插件
"""

from typing import TYPE_CHECKING

from app.crawlers.base import BaseCrawler, CrawlResult
from app.utils.url import detect_platform

if TYPE_CHECKING:
    from app.plugins.base import BasePlugin


class CrawlerFactory:
    """
    爬虫工厂
    
    负责创建和管理爬虫实例，自动选择合适的插件
    """
    
    _instances: dict[str, BaseCrawler] = {}
    
    @classmethod
    async def crawl(cls, url: str, **kwargs) -> CrawlResult:
        """
        爬取 URL 内容
        
        自动检测平台并选择合适的爬虫：
        1. 首先尝试匹配特定平台插件
        2. 如果没有匹配，使用通用插件
        
        Args:
            url: 目标 URL
            **kwargs: 额外参数
        
        Returns:
            爬取结果
        """
        from app.plugins.registry import plugin_registry
        
        platform = detect_platform(url)
        
        plugin = plugin_registry.get_plugin_for_platform(platform)
        
        if plugin and plugin.enabled:
            print(f"[CrawlerFactory] 使用 {plugin.name} 插件处理 {url}")
            return await plugin.extract(url, **kwargs)
        
        generic_plugin = plugin_registry.get_plugin("generic")
        if generic_plugin and generic_plugin.enabled:
            print(f"[CrawlerFactory] 未匹配到特定插件，使用通用插件处理 {url}")
            return await generic_plugin.extract(url, **kwargs)
        
        from app.plugins.generic.crawler import GenericCrawler
        print(f"[CrawlerFactory] 使用内置通用爬虫处理 {url}")
        crawler = GenericCrawler()
        return await crawler.extract(url, **kwargs)
    
    @classmethod
    def get_supported_platforms(cls) -> list[str]:
        """
        获取支持的平台列表
        
        Returns:
            平台名称列表
        """
        from app.plugins.registry import plugin_registry
        platforms = plugin_registry.get_supported_platforms()
        if "generic" not in platforms:
            platforms.append("generic")
        return platforms
    
    @classmethod
    def clear_instances(cls):
        """清除所有缓存的爬虫实例"""
        cls._instances.clear()


async def extract_url(url: str, **kwargs) -> CrawlResult:
    """
    提取 URL 内容的便捷函数
    
    Args:
        url: 目标 URL
        **kwargs: 额外参数
    
    Returns:
        爬取结果
    """
    return await CrawlerFactory.crawl(url, **kwargs)

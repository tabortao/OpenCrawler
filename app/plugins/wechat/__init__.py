"""
微信公众号插件

支持微信公众号文章内容的提取
"""

from .crawler import WeChatCrawler, WeChatPlugin

__all__ = ["WeChatCrawler", "WeChatPlugin"]

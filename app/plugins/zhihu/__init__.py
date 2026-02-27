"""
知乎插件

支持知乎文章、回答等内容的提取
"""

from .crawler import ZhihuCrawler, ZhihuPlugin

__all__ = ["ZhihuCrawler", "ZhihuPlugin"]

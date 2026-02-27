"""
爬虫模块

提供爬虫基类、图片下载器等
"""

from .base import BaseCrawler, CrawlResult
from .image_downloader import ImageDownloader

__all__ = [
    "BaseCrawler",
    "CrawlResult",
    "ImageDownloader",
]

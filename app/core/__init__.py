"""
核心模块

提供配置管理、异常处理、依赖注入等核心功能
"""

from .config import settings, Settings
from .exceptions import (
    CrawlerException,
    URLValidationError,
    ContentExtractionError,
    AuthenticationError,
    TimeoutError,
    PluginNotFoundError,
)

__all__ = [
    "settings",
    "Settings",
    "CrawlerException",
    "URLValidationError",
    "ContentExtractionError",
    "AuthenticationError",
    "TimeoutError",
    "PluginNotFoundError",
]

"""
插件模块

提供插件基类和注册中心
"""

from .base import BasePlugin
from .registry import PluginRegistry, plugin_registry

__all__ = [
    "BasePlugin",
    "PluginRegistry",
    "plugin_registry",
]

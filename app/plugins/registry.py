"""
插件注册中心模块

提供插件的注册、发现和管理功能
"""

import importlib
import os
from typing import Optional, Type

from app.plugins.base import BasePlugin
from app.core.exceptions import PluginNotFoundError


class PluginRegistry:
    """
    插件注册中心
    
    负责插件的注册、发现和管理
    """
    
    def __init__(self):
        self._plugins: dict[str, BasePlugin] = {}
        self._platform_mapping: dict[str, str] = {}
    
    def register(self, plugin: BasePlugin) -> None:
        """
        注册插件
        
        Args:
            plugin: 插件实例
        """
        plugin_name = plugin.name
        self._plugins[plugin_name] = plugin
        
        for platform in plugin.platforms:
            self._platform_mapping[platform] = plugin_name
        
        print(f"[PluginRegistry] 注册插件: {plugin_name}, 支持平台: {plugin.platforms}")
    
    def unregister(self, plugin_name: str) -> bool:
        """
        注销插件
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            是否成功注销
        """
        if plugin_name not in self._plugins:
            return False
        
        plugin = self._plugins[plugin_name]
        
        for platform in plugin.platforms:
            if platform in self._platform_mapping:
                del self._platform_mapping[platform]
        
        del self._plugins[plugin_name]
        print(f"[PluginRegistry] 注销插件: {plugin_name}")
        return True
    
    def get_plugin(self, plugin_name: str) -> BasePlugin:
        """
        获取插件实例
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            插件实例
        
        Raises:
            PluginNotFoundError: 插件未找到
        """
        if plugin_name not in self._plugins:
            raise PluginNotFoundError(plugin_name)
        
        return self._plugins[plugin_name]
    
    def get_plugin_for_platform(self, platform: str) -> Optional[BasePlugin]:
        """
        获取处理指定平台的插件
        
        Args:
            platform: 平台名称
        
        Returns:
            插件实例，如果未找到返回 None
        """
        if platform not in self._platform_mapping:
            return None
        
        plugin_name = self._platform_mapping[platform]
        return self._plugins.get(plugin_name)
    
    def get_all_plugins(self) -> list[BasePlugin]:
        """
        获取所有已注册的插件
        
        Returns:
            插件列表
        """
        return list(self._plugins.values())
    
    def get_enabled_plugins(self) -> list[BasePlugin]:
        """
        获取所有已启用的插件
        
        Returns:
            已启用的插件列表
        """
        return [p for p in self._plugins.values() if p.enabled]
    
    def get_supported_platforms(self) -> list[str]:
        """
        获取所有支持的平台
        
        Returns:
            平台名称列表
        """
        return list(self._platform_mapping.keys())
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        启用插件
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            是否成功
        """
        if plugin_name not in self._plugins:
            return False
        
        self._plugins[plugin_name].enable()
        return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        禁用插件
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            是否成功
        """
        if plugin_name not in self._plugins:
            return False
        
        self._plugins[plugin_name].disable()
        return True
    
    async def load_plugins_from_directory(self, directory: str) -> int:
        """
        从目录加载插件
        
        Args:
            directory: 插件目录路径
        
        Returns:
            加载的插件数量
        """
        loaded_count = 0
        
        if not os.path.exists(directory):
            return loaded_count
        
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            
            if not os.path.isdir(item_path):
                continue
            
            init_file = os.path.join(item_path, "__init__.py")
            if not os.path.exists(init_file):
                continue
            
            try:
                module_name = f"app.plugins.{item}"
                module = importlib.import_module(module_name)
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BasePlugin)
                        and attr is not BasePlugin
                    ):
                        try:
                            plugin_instance = attr()
                            self.register(plugin_instance)
                            loaded_count += 1
                        except Exception as e:
                            print(f"[PluginRegistry] 实例化插件失败 {attr_name}: {e}")
            
            except Exception as e:
                print(f"[PluginRegistry] 加载插件失败 {item}: {e}")
        
        return loaded_count
    
    async def load_all_plugins(self) -> int:
        """
        加载所有内置插件
        
        Returns:
            加载的插件数量
        """
        plugins_dir = os.path.join(os.path.dirname(__file__))
        count = await self.load_plugins_from_directory(plugins_dir)
        
        if "generic" not in self._plugins:
            try:
                from app.plugins.generic.crawler import GenericPlugin
                self.register(GenericPlugin())
                count += 1
            except Exception as e:
                print(f"[PluginRegistry] 加载通用插件失败: {e}")
        
        return count


plugin_registry = PluginRegistry()


async def initialize_plugins():
    """初始化所有插件"""
    count = await plugin_registry.load_all_plugins()
    print(f"[PluginRegistry] 共加载 {count} 个插件")
    return count


def register_plugin(plugin_class: Type[BasePlugin]) -> Type[BasePlugin]:
    """
    插件注册装饰器
    
    使用方式:
        @register_plugin
        class MyPlugin(BasePlugin):
            ...
    
    Args:
        plugin_class: 插件类
    
    Returns:
        注册的插件类
    """
    plugin_instance = plugin_class()
    plugin_registry.register(plugin_instance)
    return plugin_class

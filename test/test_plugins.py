"""测试插件初始化"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test():
    from app.plugins.registry import initialize_plugins, plugin_registry
    count = await initialize_plugins()
    print(f"加载了 {count} 个插件")
    print("已注册插件:", [p.name for p in plugin_registry.get_all_plugins()])
    print("支持的平台:", plugin_registry.get_supported_platforms())

if __name__ == "__main__":
    asyncio.run(test())

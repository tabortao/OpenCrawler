"""
测试今日头条爬虫插件

验证今日头条文章内容提取功能
"""

import asyncio
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.plugins.registry import initialize_plugins, plugin_registry
from app.utils.url import detect_platform


async def test_toutiao_plugin():
    """测试今日头条插件"""
    # 初始化插件
    await initialize_plugins()
    
    # 测试 URL
    test_url = "https://www.toutiao.com/article/7611134085859197440"
    
    # 检测平台
    platform = detect_platform(test_url)
    print(f"检测到平台: {platform}")
    
    # 获取插件
    plugin = plugin_registry.get_plugin_for_platform(platform)
    if not plugin:
        print(f"未找到平台 {platform} 的插件")
        return
    
    print(f"使用插件: {plugin.info.name} v{plugin.info.version}")
    
    try:
        # 提取内容
        result = await plugin.extract(test_url, download_images=True)
        
        print(f"\n提取结果:")
        print(f"标题: {result.title}")
        print(f"URL: {result.url}")
        print(f"图片数量: {len(result.image_urls)}")
        print(f"Markdown 长度: {len(result.markdown)}")
        
        # 保存 Markdown
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 生成文件名
        filename = f"toutiao_test_{result.title[:20].replace(' ', '_')}.md"
        filepath = os.path.join(output_dir, filename)
        
        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {result.title}\n\n")
            f.write(f"**来源:** [{result.url}]({result.url})\n\n")
            f.write(result.markdown)
        
        print(f"\nMarkdown 已保存到: {filepath}")
        print("测试成功!")
        
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_toutiao_plugin())
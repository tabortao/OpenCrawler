"""
测试通用插件优化效果

测试脚本用于验证通用插件的文章爬取能力优化效果
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.plugins.generic.crawler import GenericCrawler


async def test_specific_site(url: str):
    """测试特定网站"""
    
    print(f"\n{'='*60}")
    print(f"测试 URL: {url}")
    print('='*60)
    
    crawler = GenericCrawler()
    
    try:
        result = await crawler.extract(url)
        
        print(f"\n标题: {result.title}")
        print(f"内容长度: {len(result.markdown)} 字符")
        print(f"图片数量: {len(result.image_urls)} 张")
        
        print(f"\n图片列表:")
        for i, img_url in enumerate(result.image_urls[:10], 1):
            print(f"  {i}. {img_url}")
        
        if len(result.image_urls) > 10:
            print(f"  ... 还有 {len(result.image_urls) - 10} 张图片")
        
        print(f"\n内容预览 (前 1000 字符):")
        print("-" * 40)
        print(result.markdown[:1000])
        print("-" * 40)
        
        output_file = "test_output.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# {result.title}\n\n")
            f.write(result.markdown)
        print(f"\n完整内容已保存到: {output_file}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.ruanyifeng.com/blog/2024/03/weekly-issue-293.html"
    
    asyncio.run(test_specific_site(url))

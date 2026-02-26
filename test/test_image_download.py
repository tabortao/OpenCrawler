"""
调试图片下载问题 - 详细版本

URL: https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ
"""

import asyncio
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler import extract_url
from markdown_converter import convert_html_to_markdown, extract_images_from_html


async def test_image_download():
    url = "https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ"
    
    print(f"调试图片下载...")
    print(f"URL: {url}")
    print("-" * 50)
    
    try:
        result = await extract_url(url)
        
        html = result.get("html", "")
        markdown = result.get("markdown", "")
        image_urls = result.get("image_urls", [])
        
        print(f"标题: {result['title']}")
        print(f"HTML 长度: {len(html)}")
        print(f"原始 Markdown 长度: {len(markdown)}")
        print(f"图片 URL 数量: {len(image_urls)}")
        
        # 从 HTML 提取图片
        extracted_images = extract_images_from_html(html)
        print(f"\n从 HTML 提取的图片数量: {len(extracted_images)}")
        for i, img_url in enumerate(extracted_images[:5]):
            print(f"  {i+1}. {img_url[:80]}...")
        
        # 转换 HTML 到 Markdown
        converted_md = convert_html_to_markdown(html, platform="wechat")
        print(f"\n转换后的 Markdown 长度: {len(converted_md)}")
        
        # 检查转换后的 Markdown 中的图片引用
        img_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', converted_md)
        print(f"转换后 Markdown 中的图片引用数量: {len(img_refs)}")
        for alt, path in img_refs[:5]:
            print(f"  ![{alt}]({path[:60]}...)")
        
        # 打印转换后的 Markdown 前 500 字符
        print(f"\n转换后的 Markdown 内容预览:")
        print(converted_md[:500])
        
    except Exception as e:
        import traceback
        print(f"测试失败: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_image_download())

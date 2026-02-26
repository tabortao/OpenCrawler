"""
直接测试 convert_html_to_markdown 函数

URL: https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ
"""

import asyncio
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright
from markdown_converter import convert_html_to_markdown


async def test_convert_html_to_markdown():
    url = "https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ"
    
    print(f"直接测试 convert_html_to_markdown...")
    print(f"URL: {url}")
    print("-" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()
        page.set_default_timeout(45000)
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_load_state("domcontentloaded", timeout=20000)
            await page.wait_for_timeout(3000)
            
            el = await page.query_selector('.rich_media_content')
            if el:
                html = await el.inner_html()
                
                print(f"HTML 长度: {len(html)}")
                
                # 直接调用 convert_html_to_markdown
                markdown = convert_html_to_markdown(html, platform="wechat")
                
                print(f"Markdown 长度: {len(markdown)}")
                
                # 检查图片引用
                img_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', markdown)
                print(f"Markdown 中的图片引用数量: {len(img_refs)}")
                
                for alt, path in img_refs[:5]:
                    print(f"  ![{alt}]({path[:60]}...)")
                
                # 打印 Markdown 内容
                print(f"\nMarkdown 内容预览:")
                print(markdown[:1500])
                
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_convert_html_to_markdown())

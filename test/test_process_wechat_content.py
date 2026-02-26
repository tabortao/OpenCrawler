"""
测试 _process_wechat_content 函数

URL: https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ
"""

import asyncio
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from markdown_converter import convert_html_to_markdown


async def test_process_wechat_content():
    url = "https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ"
    
    print(f"测试 _process_wechat_content...")
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
                
                print(f"\n原始 HTML 中的 img 标签:")
                soup = BeautifulSoup(html, 'html.parser')
                print(f"  img 标签数量: {len(soup.find_all('img'))}")
                
                # 转换为 Markdown
                markdown = convert_html_to_markdown(html, platform="wechat")
                
                print(f"\n转换后的 Markdown 长度: {len(markdown)}")
                
                # 检查图片引用
                img_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', markdown)
                print(f"Markdown 中的图片引用数量: {len(img_refs)}")
                
                for alt, path in img_refs[:5]:
                    print(f"  ![{alt}]({path[:60]}...)")
                
                # 打印 Markdown 内容
                print(f"\nMarkdown 内容预览:")
                print(markdown[:1000])
                
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_process_wechat_content())

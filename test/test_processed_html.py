"""
检查处理后的 HTML 中的图片

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


async def test_processed_html():
    url = "https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ"
    
    print(f"检查处理后的 HTML...")
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
                
                soup = BeautifulSoup(html, 'html.parser')
                
                print(f"\n原始 HTML 中 img 标签数量: {len(soup.find_all('img'))}")
                
                # 手动处理图片
                for img in soup.find_all("img"):
                    data_src = img.get("data-src", "")
                    src = img.get("src", "")
                    
                    valid_data_src = data_src and not data_src.startswith("data:") and data_src != "..." and len(data_src) > 10
                    valid_src = src and not src.startswith("data:") and src != "..." and len(src) > 10
                    
                    if valid_data_src:
                        img["src"] = data_src
                        print(f"保留图片: data-src -> src")
                    elif valid_src:
                        print(f"保留图片: src 有效")
                    else:
                        print(f"移除图片: data-src='{data_src[:30]}...', src='{src[:30]}...'")
                        img.decompose()
                
                print(f"\n处理后 img 标签数量: {len(soup.find_all('img'))}")
                
                # 打印处理后的 img 标签
                for i, img in enumerate(soup.find_all('img')[:5]):
                    print(f"  img {i+1}: src='{img.get('src', '')[:60]}...'")
                
                # 转换为 Markdown
                markdown = convert_html_to_markdown(str(soup), platform="wechat")
                
                # 检查图片引用
                img_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', markdown)
                print(f"\nMarkdown 中的图片引用数量: {len(img_refs)}")
                
                for alt, path in img_refs[:5]:
                    print(f"  ![{alt}]({path[:60]}...)")
                
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_processed_html())

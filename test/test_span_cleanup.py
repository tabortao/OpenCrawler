"""
调试空 span 清理问题

URL: https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ
"""

import asyncio
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


async def test_span_cleanup():
    url = "https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ"
    
    print(f"调试空 span 清理问题...")
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
                
                soup = BeautifulSoup(html, "html.parser")
                
                # 检查 img 标签的父元素
                print(f"\n检查 img 标签的父元素:")
                for i, img in enumerate(soup.find_all('img')[:5]):
                    parent = img.parent
                    grandparent = parent.parent if parent else None
                    print(f"  img {i+1}: parent={parent.name if parent else None}, grandparent={grandparent.name if grandparent else None}")
                    if parent and parent.name == 'span':
                        print(f"    span text: '{parent.get_text(strip=True)[:50]}...'")
                        print(f"    span children: {[c.name for c in parent.children if hasattr(c, 'name')]}")
                
                # 检查包含 img 的 span
                print(f"\n检查包含 img 的 span:")
                for span in soup.find_all('span'):
                    imgs_in_span = span.find_all('img')
                    if imgs_in_span:
                        text = span.get_text(strip=True)
                        print(f"  span 包含 {len(imgs_in_span)} 个 img, text='{text[:30]}...'")
                
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_span_cleanup())

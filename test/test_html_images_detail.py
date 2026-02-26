"""
调试 HTML 中的图片详情

URL: https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ
"""

import asyncio
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


async def test_html_images_detail():
    url = "https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ"
    
    print(f"调试 HTML 中的图片详情...")
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
                
                print(f"\n所有 img 标签详情:")
                for i, img in enumerate(soup.find_all('img')):
                    src = img.get('src', '')
                    data_src = img.get('data-src', '')
                    alt = img.get('alt', '')
                    
                    src_valid = not src.startswith('data:') and src != '...' and len(src) > 10
                    data_src_valid = not data_src.startswith('data:') and data_src != '...' and len(data_src) > 10
                    
                    print(f"\n  图片 {i+1}:")
                    print(f"    src: '{src[:60]}...' (valid={src_valid})")
                    print(f"    data-src: '{data_src[:60]}...' (valid={data_src_valid})")
                    print(f"    alt: '{alt}'")
                    print(f"    最终可用URL: {data_src if data_src_valid else (src if src_valid else '无')}")
                
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_html_images_detail())

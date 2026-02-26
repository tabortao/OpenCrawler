"""
调试 _process_wechat_content 函数 - 详细版本

URL: https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ
"""

import asyncio
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


def _process_wechat_content_debug(soup):
    """
    处理微信公众号内容 - 带详细调试信息
    """
    print(f"进入 _process_wechat_content_debug")
    print(f"处理前 img 标签数量: {len(soup.find_all('img'))}")
    
    for i, img in enumerate(soup.find_all("img")):
        data_src = img.get("data-src", "")
        src = img.get("src", "")
        
        print(f"\n图片 {i+1}:")
        print(f"  data-src: '{data_src[:50]}...'")
        print(f"  src: '{src[:50]}...'")
        
        valid_data_src = data_src and not data_src.startswith("data:") and data_src != "..." and len(data_src) > 10
        valid_src = src and not src.startswith("data:") and src != "..." and len(src) > 10
        
        print(f"  valid_data_src: {valid_data_src}")
        print(f"  valid_src: {valid_src}")
        
        if valid_data_src:
            print(f"  设置 src = data_src")
            img["src"] = data_src
            print(f"  设置后 img['src']: '{img.get('src', '')[:50]}...'")
        elif valid_src:
            print(f"  保留原 src")
        else:
            print(f"  移除图片")
            img.decompose()
            continue
        
        # 清理属性
        print(f"  清理前属性: {list(img.attrs.keys())[:10]}")
        for attr in list(img.attrs.keys()):
            if attr not in ["src", "alt", "title"]:
                del img[attr]
        print(f"  清理后属性: {list(img.attrs.keys())}")
        print(f"  最终 src: '{img.get('src', '')[:50]}...'")
    
    print(f"\n处理后 img 标签数量: {len(soup.find_all('img'))}")


async def test_debug():
    url = "https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ"
    
    print(f"调试...")
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
                
                _process_wechat_content_debug(soup)
                
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_debug())

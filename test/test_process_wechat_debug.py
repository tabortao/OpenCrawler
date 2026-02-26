"""
调试 _process_wechat_content 函数处理后的 HTML

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
    处理微信公众号内容 - 带调试信息
    """
    img_count_before = len(soup.find_all('img'))
    print(f"处理前 img 标签数量: {img_count_before}")
    
    for i, img in enumerate(soup.find_all("img")):
        data_src = img.get("data-src", "")
        src = img.get("src", "")
        
        print(f"\n处理图片 {i+1}:")
        print(f"  data-src: '{data_src[:50]}...'")
        print(f"  src: '{src[:50]}...'")
        
        if data_src and not data_src.startswith("data:") and data_src != "...":
            img["src"] = data_src
            print(f"  -> 设置 src = data-src")
        elif src and (src.startswith("data:") or src == "..."):
            print(f"  -> 移除图片 (无效 src)")
            img.decompose()
            continue
        
        for attr in list(img.attrs.keys()):
            if attr not in ["src", "alt", "title"]:
                del img[attr]
        
        print(f"  处理后 src: '{img.get('src', '')[:50]}...'")
    
    img_count_after = len(soup.find_all('img'))
    print(f"\n处理后 img 标签数量: {img_count_after}")
    
    return soup


async def test_process_wechat_content():
    url = "https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ"
    
    print(f"调试 _process_wechat_content...")
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
                
                _process_wechat_content_debug(soup)
                
                # 保存处理后的 HTML
                with open('test/debug_processed_html.html', 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                print(f"\n处理后的 HTML 已保存到 test/debug_processed_html.html")
                
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_process_wechat_content())

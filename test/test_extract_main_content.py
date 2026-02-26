"""
调试 _extract_main_content 函数

URL: https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ
"""

import asyncio
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from markdown_converter import extract_images_from_html


async def test_extract_main_content():
    url = "https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ"
    
    print(f"调试 _extract_main_content...")
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
            
            # 测试不同的选择器
            selectors = ['.rich_media_content', '#js_content']
            
            for selector in selectors:
                print(f"\n测试选择器: {selector}")
                el = await page.query_selector(selector)
                if el:
                    text = await el.inner_text()
                    html = await el.inner_html()
                    print(f"  找到元素!")
                    print(f"  文本长度: {len(text)}")
                    print(f"  HTML 长度: {len(html)}")
                    
                    # 检查 HTML 中的图片
                    soup = BeautifulSoup(html, 'html.parser')
                    imgs = soup.find_all('img')
                    print(f"  img 标签数量: {len(imgs)}")
                    
                    for i, img in enumerate(imgs[:5]):
                        src = img.get('src', '')
                        data_src = img.get('data-src', '')
                        print(f"    {i+1}. src='{src[:50]}...', data-src='{data_src[:50]}...'")
                    
                    # 使用 extract_images_from_html 提取图片
                    image_urls = extract_images_from_html(html)
                    print(f"  extract_images_from_html 结果: {len(image_urls)} 张图片")
                    
                    if len(imgs) > 0:
                        print(f"\n  保存 HTML 到 test/debug_main_content.html")
                        with open('test/debug_main_content.html', 'w', encoding='utf-8') as f:
                            f.write(html)
                        break
                else:
                    print(f"  未找到元素")
            
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_extract_main_content())

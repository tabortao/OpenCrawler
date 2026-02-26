"""
测试迭代器问题

URL: https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ
"""

import asyncio
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


def _process_wechat_content_fixed(soup):
    """
    处理微信公众号内容 - 修复迭代器问题
    """
    # 先收集所有 img 标签到列表
    imgs = list(soup.find_all("img"))
    
    print(f"处理前 img 标签数量: {len(imgs)}")
    
    for img in imgs:
        data_src = img.get("data-src", "")
        src = img.get("src", "")
        
        valid_data_src = data_src and not data_src.startswith("data:") and data_src != "..." and len(data_src) > 10
        valid_src = src and not src.startswith("data:") and src != "..." and len(src) > 10
        
        if valid_data_src:
            img["src"] = data_src
        elif valid_src:
            pass
        else:
            img.decompose()
            continue
        
        for attr in list(img.attrs.keys()):
            if attr not in ["src", "alt", "title"]:
                del img[attr]
    
    print(f"处理后 img 标签数量: {len(soup.find_all('img'))}")
    
    # 打印处理后的 img 标签
    for i, img in enumerate(soup.find_all('img')[:5]):
        print(f"  img {i+1}: src='{img.get('src', '')[:60]}...'")


async def test_fixed():
    url = "https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ"
    
    print(f"测试修复后的函数...")
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
                
                _process_wechat_content_fixed(soup)
                
                # 检查转换后的 HTML
                processed_html = str(soup)
                
                # 检查 img 标签
                img_pattern = r'<img[^>]+>'
                img_tags = re.findall(img_pattern, processed_html)
                print(f"\n处理后 HTML 中的 img 标签数量: {len(img_tags)}")
                
                for i, img_tag in enumerate(img_tags[:5]):
                    print(f"  img {i+1}: {img_tag[:100]}...")
                
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_fixed())

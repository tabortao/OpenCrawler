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
    print(f"=== 开始处理 ===")
    
    imgs = list(soup.find_all("img"))
    print(f"找到 {len(imgs)} 个 img 标签")
    
    for i, img in enumerate(imgs):
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
            img["src"] = data_src
            print(f"  -> 设置 src = data_src")
        elif valid_src:
            print(f"  -> 保留原 src")
        else:
            print(f"  -> 移除图片")
            img.decompose()
            continue
        
        print(f"  清理前属性: {list(img.attrs.keys())}")
        for attr in list(img.attrs.keys()):
            if attr not in ["src", "alt", "title"]:
                del img[attr]
        print(f"  清理后属性: {list(img.attrs.keys())}")
        print(f"  最终 src: '{img.get('src', '')[:50]}...'")
    
    print(f"\n=== 处理 img 后 ===")
    print(f"剩余 img 标签数量: {len(soup.find_all('img'))}")
    
    # 打印剩余的 img 标签
    for i, img in enumerate(soup.find_all('img')[:5]):
        print(f"  img {i+1}: src='{img.get('src', '')[:60]}...'")
    
    # 继续处理其他内容
    for br in soup.find_all("br"):
        br.replace_with("\n")
    
    for tag in soup.find_all(["mp-style-type", "mp-common-profile", "mpvideosnap"]):
        tag.decompose()
    
    for tag in soup.find_all(class_=["js_video_play", "video_iframe", "rich_media_video"]):
        tag.decompose()
    
    print(f"\n=== 处理其他标签后 ===")
    print(f"剩余 img 标签数量: {len(soup.find_all('img'))}")
    
    # 检查 span 处理
    print(f"\n=== 处理 span ===")
    spans = list(soup.find_all("span"))
    print(f"找到 {len(spans)} 个 span 标签")
    
    for span in spans:
        textstyle = span.get("textstyle")
        style = span.get("style", "")
        
        if textstyle is not None and "font-weight" in style and "bold" in style:
            text = span.get_text(strip=True)
            print(f"  发现标题: '{text}'")
            
            if len(text) < 2 or len(text) > 100:
                print(f"    -> 跳过 (长度不符合)")
                continue
            
            font_size_match = re.search(r'font-size:\s*(\d+)px', style)
            font_size = int(font_size_match.group(1)) if font_size_match else 0
            
            if font_size >= 17:
                h2_tag = soup.new_tag("h2")
                h2_tag.string = text
                span.replace_with(h2_tag)
                print(f"    -> 转换为 h2")
            elif font_size >= 16:
                h3_tag = soup.new_tag("h3")
                h3_tag.string = text
                span.replace_with(h3_tag)
                print(f"    -> 转换为 h3")
    
    print(f"\n=== 处理标题后 ===")
    print(f"剩余 img 标签数量: {len(soup.find_all('img'))}")
    
    for span in soup.find_all("span"):
        if not span.get_text(strip=True):
            span.decompose()
    
    for tag in soup.find_all(id=["js_content_video", "js_player"]):
        tag.decompose()
    
    print(f"\n=== 最终结果 ===")
    print(f"剩余 img 标签数量: {len(soup.find_all('img'))}")
    
    for i, img in enumerate(soup.find_all('img')[:5]):
        print(f"  img {i+1}: src='{img.get('src', '')[:60]}...'")


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

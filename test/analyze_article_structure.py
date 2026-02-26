"""
分析微信公众号文章的 HTML 结构 - 更详细版本

分析 URL: https://mp.weixin.qq.com/s/kosxCq8j9y3J8pF_CRvecg
"""

import asyncio
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def analyze_article_structure():
    url = "https://mp.weixin.qq.com/s/kosxCq8j9y3J8pF_CRvecg"
    
    print(f"分析文章: {url}")
    print("=" * 60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        page.set_default_timeout(45000)
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_load_state("domcontentloaded", timeout=20000)
            page.wait_for_timeout(3000)
            
            content_el = page.query_selector('#js_content')
            if content_el:
                html = content_el.inner_html()
            else:
                html = page.content()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            print("\n1. 查找所有 strong 标签:")
            print("-" * 40)
            for i, tag in enumerate(soup.find_all('strong')[:30]):
                text = tag.get_text(strip=True)
                if len(text) > 3 and len(text) < 50:
                    parent = tag.parent
                    grandparent = parent.parent if parent else None
                    print(f"  strong: '{text}'")
                    print(f"    parent: {parent.name if parent else None}, attrs={dict(parent.attrs) if parent else {}}")
                    if grandparent:
                        print(f"    grandparent: {grandparent.name}, attrs={dict(grandparent.attrs)}")
            
            print("\n2. 查找所有带 font-weight 的 style:")
            print("-" * 40)
            for el in soup.find_all(style=True):
                style = el.get('style', '')
                if 'font-weight' in style or 'bold' in style.lower():
                    text = el.get_text(strip=True)[:50]
                    print(f"  {el.name}: style='{style[:80]}...', text='{text}'")
            
            print("\n3. 查找所有带 textstyle 属性的元素:")
            print("-" * 40)
            for el in soup.find_all(attrs={'textstyle': True}):
                text = el.get_text(strip=True)[:50]
                style = el.get('style', '')[:80]
                print(f"  {el.name}: textstyle='{el.get('textstyle')}', style='{style}', text='{text}'")
            
            print("\n4. 查找所有带 leaf 属性的元素:")
            print("-" * 40)
            for el in soup.find_all(attrs={'leaf': True})[:20]:
                text = el.get_text(strip=True)[:50]
                style = el.get('style', '')[:80]
                print(f"  {el.name}: leaf='{el.get('leaf')}', style='{style}', text='{text}'")
            
            print("\n5. 分析特定文本周围的 HTML 结构:")
            print("-" * 40)
            target_texts = ['新模型', '流水线', '量化', '小结']
            
            for target in target_texts:
                for el in soup.find_all(string=re.compile(re.escape(target))):
                    if len(el.strip()) < 30:
                        parent = el.parent
                        grandparent = parent.parent if parent else None
                        great_grandparent = grandparent.parent if grandparent else None
                        print(f"\n  找到: '{el.strip()}'")
                        print(f"    父元素: {parent.name}, attrs={dict(parent.attrs)}")
                        if grandparent:
                            print(f"    祖父元素: {grandparent.name}, attrs={dict(grandparent.attrs)}")
                        if great_grandparent:
                            print(f"    曾祖父元素: {great_grandparent.name}, attrs={dict(great_grandparent.attrs)}")
            
            print("\n6. 保存原始 HTML 到文件:")
            print("-" * 40)
            with open('test/article_html_full.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("  已保存到 test/article_html_full.html")
            
            return html
            
        finally:
            browser.close()


if __name__ == "__main__":
    analyze_article_structure()

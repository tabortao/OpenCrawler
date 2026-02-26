"""
调试 HTML 中的图片

URL: https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ
"""

import asyncio
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler import extract_url
from bs4 import BeautifulSoup


async def test_html_images():
    url = "https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ"
    
    print(f"调试 HTML 中的图片...")
    print(f"URL: {url}")
    print("-" * 50)
    
    try:
        result = await extract_url(url)
        
        html = result.get("html", "")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找所有 img 标签
        print(f"\n查找所有 img 标签:")
        for i, img in enumerate(soup.find_all('img')[:10]):
            src = img.get('src', '')
            data_src = img.get('data-src', '')
            alt = img.get('alt', '')
            print(f"  {i+1}. src='{src[:50]}...', data-src='{data_src[:50]}...', alt='{alt}'")
        
        # 保存 HTML 到文件
        with open('test/debug_html.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\nHTML 已保存到 test/debug_html.html")
        
        # 查找包含 "下图" 或 "效果" 的段落
        print(f"\n查找包含 '下图' 或 '效果' 的内容:")
        for p in soup.find_all('p'):
            text = p.get_text()
            if '下图' in text or '效果' in text:
                print(f"  段落: {text[:100]}...")
                # 查找相邻的图片
                next_sibling = p.find_next_sibling()
                if next_sibling:
                    img = next_sibling.find('img')
                    if img:
                        print(f"    相邻图片: src='{img.get('src', '')[:50]}...', data-src='{img.get('data-src', '')[:50]}...'")
        
    except Exception as e:
        import traceback
        print(f"测试失败: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_html_images())

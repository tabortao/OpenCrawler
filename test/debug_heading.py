"""
调试微信样式标题转换
"""

import re
from bs4 import BeautifulSoup

html = '''
<p style="line-height: 1.75em;margin-bottom: 24px;margin-top: 24px;">
    <span leaf="">
        <span textstyle="" style="font-size: 17px;color: rgb(0, 128, 255);font-weight: bold;">小结</span>
    </span>
</p>
'''

soup = BeautifulSoup(html, 'html.parser')

print("原始 HTML:")
print(soup.prettify())
print()

print("查找符合条件的 span:")
for span in soup.find_all("span"):
    textstyle = span.get("textstyle")
    style = span.get("style", "")
    
    print(f"  span: textstyle={textstyle}, style='{style[:50]}...'")
    
    if textstyle is not None and "font-weight" in style and "bold" in style:
        text = span.get_text(strip=True)
        print(f"    -> 符合条件! text='{text}'")
        
        font_size_match = re.search(r'font-size:\s*(\d+)px', style)
        font_size = int(font_size_match.group(1)) if font_size_match else 0
        print(f"    -> font_size={font_size}")

print("\n模拟转换过程:")
spans = list(soup.find_all("span"))
print(f"找到 {len(spans)} 个 span")

for span in spans:
    textstyle = span.get("textstyle")
    style = span.get("style", "")
    
    if textstyle is not None and "font-weight" in style and "bold" in style:
        text = span.get_text(strip=True)
        
        if len(text) < 3 or len(text) > 100:
            print(f"  跳过: '{text}' (长度不符合)")
            continue
        
        font_size_match = re.search(r'font-size:\s*(\d+)px', style)
        font_size = int(font_size_match.group(1)) if font_size_match else 0
        
        print(f"  转换: '{text}', font_size={font_size}")
        
        if font_size >= 17:
            h2_tag = soup.new_tag("h2")
            h2_tag.string = text
            span.replace_with(h2_tag)
            print(f"    -> 替换为 h2")

print("\n转换后 HTML:")
print(soup.prettify())

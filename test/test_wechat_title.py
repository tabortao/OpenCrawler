"""
测试微信公众号标题提取
"""

import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://mp.weixin.qq.com/s/FDZZo5hzPpGju-bzTs8kNQ', wait_until='domcontentloaded')
        await page.wait_for_timeout(3000)
        
        # 检查标题元素
        title_el = await page.query_selector('#activity-name')
        if title_el:
            text = await title_el.inner_text()
            print(f'activity-name: {text}')
        else:
            print('activity-name not found')
        
        # 检查 rich_media_title
        title_el2 = await page.query_selector('.rich_media_title')
        if title_el2:
            text2 = await title_el2.inner_text()
            print(f'rich_media_title: {text2}')
        else:
            print('rich_media_title not found')
        
        # 检查 og:title
        og_title = await page.evaluate('''() => {
            const el = document.querySelector('meta[property="og:title"]');
            return el ? el.content : null;
        }''')
        print(f'og:title: {og_title}')
        
        # 获取页面标题
        page_title = await page.title()
        print(f'page title: {page_title}')
        
        # 获取 HTML 内容检查
        html = await page.content()
        
        # 检查 meta 标签
        import re
        og_match = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if og_match:
            print(f'og:title from html: {og_match.group(1)}')
        else:
            print('og:title not found in html')
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test())

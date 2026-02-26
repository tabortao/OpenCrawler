"""
测试少数派网站图片提取

分析少数派文章的 HTML 结构，找出图片存储方式
"""
import asyncio
from playwright.async_api import async_playwright


async def analyze_sspai_images():
    """分析少数派文章的图片结构"""
    url = "https://sspai.com/post/106488"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print(f"正在访问: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 滚动页面加载懒加载图片
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(500)
            
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)
            
            # 提取所有图片信息
            images_info = await page.evaluate("""
                () => {
                    const imgs = document.querySelectorAll('img');
                    return Array.from(imgs).map((img, index) => {
                        const attrs = {};
                        for (let attr of img.attributes) {
                            attrs[attr.name] = attr.value;
                        }
                        return {
                            index: index,
                            tagName: img.tagName,
                            className: img.className,
                            src: img.src || '',
                            dataset: {...img.dataset},
                            attributes: attrs,
                            outerHTML: img.outerHTML.substring(0, 500)
                        };
                    });
                }
            """)
            
            print(f"\n找到 {len(images_info)} 个图片元素")
            print("=" * 80)
            
            for img in images_info:
                print(f"\n图片 #{img['index'] + 1}:")
                print(f"  class: {img['className']}")
                print(f"  src: {img['src'][:100] if img['src'] else 'N/A'}...")
                print(f"  data-* 属性:")
                for key, value in img['dataset'].items():
                    if value and len(value) > 10:
                        print(f"    data-{key}: {value[:100]}...")
                print(f"  所有属性:")
                for key, value in img['attributes'].items():
                    if value and len(str(value)) > 10 and key not in ['src', 'class']:
                        print(f"    {key}: {str(value)[:100]}...")
                print(f"  HTML 片段: {img['outerHTML'][:200]}...")
            
            # 查找文章主体内容选择器
            content_selectors = [
                '.article-content',
                '.content',
                'article',
                '.post-content',
                '.article-body',
                '#article-content',
            ]
            
            print("\n\n尝试查找文章主体内容:")
            print("=" * 80)
            
            for selector in content_selectors:
                el = await page.query_selector(selector)
                if el:
                    text = await el.inner_text()
                    if len(text) > 100:
                        print(f"找到内容选择器: {selector}, 文本长度: {len(text)}")
                        
                        # 提取该区域内的图片
                        content_images = await el.evaluate("""
                            (el) => {
                                const imgs = el.querySelectorAll('img');
                                return Array.from(imgs).map((img) => {
                                    const attrs = {};
                                    for (let attr of img.attributes) {
                                        attrs[attr.name] = attr.value;
                                    }
                                    return {
                                        src: img.src || '',
                                        dataset: {...img.dataset},
                                        attributes: attrs
                                    };
                                });
                            }
                        """)
                        
                        print(f"  该区域内有 {len(content_images)} 个图片")
                        for i, cimg in enumerate(content_images[:3]):
                            print(f"  图片 {i+1}:")
                            print(f"    src: {cimg['src'][:80] if cimg['src'] else 'N/A'}...")
                            for key, value in cimg['dataset'].items():
                                if value and len(value) > 10:
                                    print(f"    data-{key}: {value[:80]}...")
                        break
            
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(analyze_sspai_images())

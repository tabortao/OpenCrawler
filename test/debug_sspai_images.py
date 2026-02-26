"""
调试少数派文章图片下载
"""
import asyncio
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler import WebCrawler, ImageDownloader, html_to_markdown_with_images
from markdown_converter import convert_html_to_markdown, extract_images_from_html, process_images_in_markdown


async def debug_sspai_images():
    """调试少数派文章图片下载"""
    url = "https://sspai.com/post/106488"
    
    # 爬取页面
    crawler = WebCrawler()
    result = await crawler.crawl(url)
    
    print(f"标题: {result['title']}")
    print(f"HTML 长度: {len(result['html'])}")
    print(f"图片 URL 数量: {len(result['image_urls'])}")
    
    # 提取图片 URL
    image_urls = extract_images_from_html(result['html'])
    print(f"\n从 HTML 提取的图片 URL 数量: {len(image_urls)}")
    for i, img_url in enumerate(image_urls[:5]):
        print(f"  {i+1}. {img_url[:80]}...")
    
    # 转换 HTML 到 Markdown
    markdown = convert_html_to_markdown(result['html'], platform='sspai')
    print(f"\nMarkdown 长度: {len(markdown)}")
    
    # 检查 Markdown 中的图片
    img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    matches = re.findall(img_pattern, markdown)
    print(f"\nMarkdown 中的图片数量: {len(matches)}")
    for i, (alt, url) in enumerate(matches[:5]):
        print(f"  {i+1}. [{alt}]({url[:80]}...)")
    
    # 测试图片下载
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    downloader = ImageDownloader(output_dir)
    
    print("\n测试下载前 3 个图片:")
    for i, img_url in enumerate(image_urls[:3]):
        print(f"  下载 {i+1}: {img_url[:60]}...")
        local_path = downloader.download_image(img_url)
        if local_path:
            print(f"    成功: {local_path}")
        else:
            print(f"    失败")
    
    downloader.close()
    
    # 测试完整的图片处理流程
    print("\n测试完整的图片处理流程:")
    markdown_with_images = html_to_markdown_with_images(result['html'], image_urls, output_dir, platform='sspai')
    
    # 检查处理后的 Markdown 中的图片
    matches_after = re.findall(img_pattern, markdown_with_images)
    print(f"处理后的 Markdown 中的图片数量: {len(matches_after)}")
    for i, (alt, url) in enumerate(matches_after[:5]):
        print(f"  {i+1}. [{alt}]({url})")


if __name__ == "__main__":
    asyncio.run(debug_sspai_images())

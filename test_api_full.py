import asyncio
import sys

sys.path.insert(0, '.')
from crawler import extract_url, save_article

async def test():
    url = "http://xhslink.com/o/5Msx6KHENIf"
    
    print("=== Testing extract_url ===")
    result = await extract_url(url)
    
    print(f"Status: {result.get('status')}")
    print(f"Title: {result.get('title')}")
    print(f"Markdown length: {len(result.get('markdown', ''))}")
    print(f"Image URLs count: {len(result.get('image_urls', []))}")
    
    print("\n=== Full Markdown ===")
    print(result.get('markdown', ''))
    
    print("\n=== Testing save_article with download_images=True ===")
    filepath = save_article(
        title=result["title"],
        url=result["url"],
        markdown=result["markdown"],
        html=result.get("html", ""),
        image_urls=result.get("image_urls", []),
        download_images=True,
    )
    print(f"Saved to: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"\n=== Saved file content ===")
    print(content)

asyncio.run(test())

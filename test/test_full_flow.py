import asyncio
import sys
sys.path.insert(0, '.')

from crawler import extract_url, save_article

async def test():
    url = "http://xhslink.com/o/5Msx6KHENIf"
    print(f"Testing full flow with URL: {url}")
    
    result = await extract_url(url)
    print(f"\n=== extract_url result ===")
    print(f"Status: {result.get('status')}")
    print(f"Title: {result.get('title')}")
    print(f"Markdown length: {len(result.get('markdown', ''))}")
    print(f"Image URLs: {len(result.get('image_urls', []))}")
    
    print(f"\n=== Calling save_article ===")
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
    print(f"\n=== Saved file content ({len(content)} chars) ===")
    print(content)

asyncio.run(test())

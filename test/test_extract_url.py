import asyncio
import sys
sys.path.insert(0, '.')

from crawler import extract_url

async def test():
    url = "http://xhslink.com/o/5Msx6KHENIf"
    print(f"Testing extract_url with URL: {url}")
    
    try:
        result = await extract_url(url)
        print(f"\n=== Result ===")
        print(f"Status: {result.get('status')}")
        print(f"Title: {result.get('title')}")
        print(f"URL: {result.get('url')}")
        print(f"Markdown length: {len(result.get('markdown', ''))}")
        print(f"Image URLs: {result.get('image_urls', [])}")
        print(f"\n=== Markdown ===")
        print(result.get('markdown', '')[:1000])
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

asyncio.run(test())

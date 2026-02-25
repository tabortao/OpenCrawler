import asyncio
import sys
sys.path.insert(0, '.')

from xhs_crawler import crawl_xiaohongshu

async def test():
    url = "http://xhslink.com/o/5Msx6KHENIf"
    print(f"Testing XiaoHongShu crawler with URL: {url}")
    
    try:
        result = await crawl_xiaohongshu(url, headless=True)
        print(f"\n=== Result ===")
        print(f"Title: {result.get('title')}")
        print(f"URL: {result.get('url')}")
        print(f"Markdown length: {len(result.get('markdown', ''))}")
        print(f"Images: {len(result.get('note', {}).get('image_list', []))}")
        print(f"\n=== Markdown ===")
        print(result.get('markdown', '')[:1000])
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

asyncio.run(test())

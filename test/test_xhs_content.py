import asyncio
from xhs_crawler import crawl_xiaohongshu

url = "http://xhslink.com/o/5Msx6KHENIf"

async def test():
    result = await crawl_xiaohongshu(url, headless=True)
    print("Title:", result["title"])
    print("\n=== Full Markdown ===")
    print(result["markdown"])

asyncio.run(test())

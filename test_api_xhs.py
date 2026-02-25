import asyncio
from crawler import WebCrawler

async def test():
    c = WebCrawler()
    result = await c.crawl("http://xhslink.com/o/5Msx6KHENIf")
    print("Status:", result.get("status"))
    print("Title:", result.get("title"))
    print("\n=== Markdown ===")
    print(result.get("markdown", "")[:2000])

asyncio.run(test())

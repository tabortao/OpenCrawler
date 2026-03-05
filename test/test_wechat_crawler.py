"""
测试微信公众号爬虫
"""

import asyncio
from app.plugins.wechat.crawler import WeChatCrawler

async def test():
    crawler = WeChatCrawler()
    result = await crawler.extract('https://mp.weixin.qq.com/s/FDZZo5hzPpGju-bzTs8kNQ')
    print(f'Title: {result.title}')
    print(f'Content length: {len(result.markdown)} chars')
    print(f'Images: {len(result.image_urls)}')
    print(f'Content preview: {result.markdown[:500]}...')

if __name__ == '__main__':
    asyncio.run(test())

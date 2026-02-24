from crawler import WebCrawler
import asyncio
import re

c = WebCrawler()
result = asyncio.run(c.crawl('https://mp.weixin.qq.com/s/aLEfwYpIRYFTJER8EdjeWg'))
markdown = result.get('markdown', '')
print('Markdown length:', len(markdown))

imgs = re.findall(r'!\[[^\]]*\]\([^)]+\)', markdown)
print('Found images in markdown:', len(imgs))
for img in imgs[:5]:
    print(img[:150])

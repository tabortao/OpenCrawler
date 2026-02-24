from crawler import WebCrawler, save_article
import asyncio

url = 'https://mp.weixin.qq.com/s/0JG7ekoccG0YiSLmKSZU3Q'
c = WebCrawler()
result = asyncio.run(c.crawl(url))

print('Title:', result.get('title'))
print('Markdown length:', len(result.get('markdown', '')))
print('Image URLs:', len(result.get('image_urls', [])))
print('Image URLs:', result.get('image_urls', []))

filepath = save_article(
    title=result['title'],
    url=result['url'],
    markdown=result['markdown'],
    html=result.get('html', ''),
    image_urls=result.get('image_urls', []),
    download_images=True
)

print(f'\nSaved to: {filepath}')

import os
images_dir = os.path.join('output', 'images')
if os.path.exists(images_dir):
    files = os.listdir(images_dir)
    print(f'Images in output/images: {len(files)}')
    for f in files:
        print(f'  - {f}')

import re
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()
    imgs = re.findall(r'!\[[^\]]*\]\([^)]+\)', content)
    print(f'\nImages in MD: {len(imgs)}')
    for img in imgs:
        print(f'  - {img}')

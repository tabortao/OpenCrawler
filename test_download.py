from crawler import WebCrawler, ImageDownloader, process_images_in_markdown
import asyncio
import os

url = 'https://mp.weixin.qq.com/s/0JG7ekoccG0YiSLmKSZU3Q'
c = WebCrawler()
result = asyncio.run(c.crawl(url))
markdown = result.get('markdown', '')
image_urls = result.get('image_urls', [])

print('Title:', result.get('title'))
print('Markdown length:', len(markdown))
print('Image URLs:', len(image_urls))

print('\n=== Image URLs ===')
for i, url in enumerate(image_urls[:5]):
    print(f'{i+1}. {url[:100]}...')

print('\n=== Testing download ===')
output_dir = 'output/test_article'
os.makedirs(output_dir, exist_ok=True)

result_md = process_images_in_markdown(markdown, image_urls, output_dir)
print('Result length:', len(result_md))
print('Has images:', '![' in result_md)

images_dir = os.path.join(output_dir, 'images')
if os.path.exists(images_dir):
    files = os.listdir(images_dir)
    print(f'\nDownloaded {len(files)} images:')
    for f in files[:5]:
        print(f'  - {f}')
else:
    print('\nNo images directory!')

print('\n=== Markdown preview ===')
print(result_md[:2000])

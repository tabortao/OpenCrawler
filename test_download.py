from crawler import WebCrawler, ImageDownloader, process_images_in_markdown
import asyncio

c = WebCrawler()
result = asyncio.run(c.crawl('https://mp.weixin.qq.com/s/8nKpBlvDEkQda1PsRYT5SQ'))
markdown = result.get('markdown', '')
image_urls = result.get('image_urls', [])

print('Markdown length:', len(markdown))
print('Image URLs:', len(image_urls))

print('\n=== Testing image download ===')
downloader = ImageDownloader('output/test')
for i, url in enumerate(image_urls[:3]):
    print(f'\nDownloading image {i+1}:')
    print(f'URL: {url[:100]}...')
    local_path = downloader.download_image(url)
    print(f'Local path: {local_path}')

downloader.close()

print('\n=== Testing process_images_in_markdown ===')
result_md = process_images_in_markdown(markdown, image_urls, 'output/test')
print('Result length:', len(result_md))
print('Has images:', '![' in result_md)

def process_images_in_markdown(markdown: str, image_urls: list[str], output_dir: str) -> str:
    if not markdown and not image_urls:
        return markdown

    downloader = ImageDownloader(output_dir)

    try:
        for i, img_url in enumerate(image_urls):
            if not img_url or img_url.startswith("data:"):
                continue

            img_url = img_url.replace("&amp;", "&")
            img_url = img_url.replace("&lt;", "<")
            img_url = img_url.replace("&gt;", ">")
            img_url = img_url.replace("&quot;", '"')

            local_path = downloader.download_image(img_url)
            if local_path:
                markdown += f"\n\n![图片{i+1}]({local_path})"

        return markdown

    finally:
        downloader.close()

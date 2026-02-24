import asyncio
import hashlib
import os
import re
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
from dotenv import load_dotenv
from trafilatura import extract

from utils import (
    clean_markdown,
    detect_platform,
    extract_title_from_html,
    get_platform_config,
    parse_cookie_string,
    sanitize_filename,
)

load_dotenv()

PROXY_URL = os.getenv("PROXY_URL", "")
ZHIHU_COOKIE = os.getenv("ZHIHU_COOKIE", "")
XHS_COOKIE = os.getenv("XHS_COOKIE", "")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")


class ImageDownloader:
    def __init__(self, output_dir: str):
        self.images_dir = os.path.join(output_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        self.client = httpx.Client(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            },
        )
        self.downloaded: dict[str, str] = {}

    def _get_image_extension(self, url: str, content_type: str = "") -> str:
        if content_type:
            if "webp" in content_type:
                return ".webp"
            elif "png" in content_type:
                return ".png"
            elif "gif" in content_type:
                return ".gif"
            elif "jpeg" in content_type or "jpg" in content_type:
                return ".jpg"

        parsed = urlparse(url)
        path = parsed.path.lower()
        for ext in [".webp", ".png", ".gif", ".jpg", ".jpeg"]:
            if path.endswith(ext):
                return ext

        return ".jpg"

    def download_image(self, url: str) -> str | None:
        if url in self.downloaded:
            return self.downloaded[url]

        try:
            response = self.client.get(url)
            if response.status_code != 200:
                return None

            content_type = response.headers.get("content-type", "")
            ext = self._get_image_extension(url, content_type)

            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            filename = f"{url_hash}{ext}"
            filepath = os.path.join(self.images_dir, filename)

            with open(filepath, "wb") as f:
                f.write(response.content)

            relative_path = f"images/{filename}"
            self.downloaded[url] = relative_path
            return relative_path

        except Exception:
            return None

    def close(self):
        self.client.close()


class WebCrawler:
    def __init__(self):
        self.result: dict[str, Any] = {}
        self.error: str | None = None
        self.platform = "generic"

    def _get_cookies_for_platform(self, platform: str) -> list[dict[str, Any]]:
        cookies_to_inject: list[dict[str, Any]] = []

        if platform == "zhihu" and ZHIHU_COOKIE:
            cookies_to_inject = parse_cookie_string(ZHIHU_COOKIE)
            for cookie in cookies_to_inject:
                cookie["domain"] = ".zhihu.com"
        elif platform == "xiaohongshu" and XHS_COOKIE:
            cookies_to_inject = parse_cookie_string(XHS_COOKIE)
            for cookie in cookies_to_inject:
                cookie["domain"] = ".xiaohongshu.com"

        return cookies_to_inject

    async def _scroll_page(self, page, times: int) -> None:
        if times <= 0:
            return

        for _ in range(times):
            try:
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(0.4)
            except Exception:
                break

        try:
            await page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass

    async def _handle_zhihu_popup(self, page) -> None:
        close_selectors = [
            '.Modal-closeButton',
            'button[aria-label="关闭"]',
            '.CloseIcon',
        ]
        for sel in close_selectors:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    is_visible = await btn.is_visible()
                    if is_visible:
                        await btn.click()
                        await asyncio.sleep(0.3)
                        break
            except Exception:
                continue

    async def _extract_main_content(self, page, platform: str) -> str:
        selectors_map = {
            "zhihu": [
                '.Post-RichTextContainer',
                '.Post-RichText',
                '.RichText',
                '.RichContent-inner',
                'article',
                '.ztext',
            ],
            "github": ['.markdown-body', 'article', '.readme'],
            "xiaohongshu": ['.note-content', '#detail-desc', '.content'],
            "wechat": ['.rich_media_content', '#js_content'],
            "generic": ['article', '.content', '.post', 'main'],
        }

        selectors = selectors_map.get(platform, selectors_map["generic"])

        for selector in selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    text = await el.inner_text()
                    if len(text) > 100:
                        html = await el.inner_html()
                        if platform == "wechat":
                            html = await self._process_wechat_images(el)
                        return html
            except Exception:
                continue

        try:
            return await page.content()
        except Exception:
            return ""

    async def _process_wechat_images(self, element) -> str:
        try:
            await element.evaluate("""
                (el) => {
                    const images = el.querySelectorAll('img');
                    images.forEach(img => {
                        const dataSrc = img.getAttribute('data-src');
                        if (dataSrc && !img.getAttribute('src')) {
                            img.setAttribute('src', dataSrc);
                        }
                    });
                }
            """)
            return await element.inner_html()
        except Exception:
            return await element.inner_html()

    def _inject_wechat_images(self, markdown: str, html: str) -> str:
        img_pattern = r'<img[^>]+data-src=["\']([^"\']+)["\'][^>]*>'
        matches = re.findall(img_pattern, html, re.IGNORECASE)

        if not matches:
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            matches = re.findall(img_pattern, html, re.IGNORECASE)

        image_markdown = ""
        for i, img_url in enumerate(matches[:20]):
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            if "mmbiz.qpic.cn" in img_url or "wx" in img_url:
                clean_url = img_url.split("&amp;")[0].split("#")[0]
                image_markdown += f"\n\n![图片{i+1}]({clean_url})\n"

        if image_markdown and markdown:
            return markdown + "\n\n---\n\n## 图片内容\n" + image_markdown
        return markdown

    async def crawl(self, url: str) -> dict[str, Any]:
        self.platform = detect_platform(url)
        self.result = {}
        self.error = None
        config = get_platform_config(self.platform)

        crawler = PlaywrightCrawler(
            max_requests_per_crawl=1,
            headless=True,
            browser_type="chromium",
            request_handler_timeout=timedelta(seconds=120),
        )

        crawler_instance = self

        @crawler.router.default_handler
        async def request_handler(context: PlaywrightCrawlingContext) -> None:
            page = context.page

            cookies = crawler_instance._get_cookies_for_platform(crawler_instance.platform)
            if cookies:
                await page.context.add_cookies(cookies)

            try:
                await page.wait_for_load_state("domcontentloaded", timeout=25000)

                if crawler_instance.platform == "zhihu":
                    await asyncio.sleep(1.5)
                    await crawler_instance._handle_zhihu_popup(page)
                    await asyncio.sleep(0.5)

                await crawler_instance._scroll_page(page, config["scroll_times"])
                await asyncio.sleep(0.5)

                html_content = await page.content()
                title = extract_title_from_html(html_content)

                main_content = await crawler_instance._extract_main_content(page, crawler_instance.platform)

                markdown = extract(main_content, include_links=True, include_images=True)
                markdown = clean_markdown(markdown) if markdown else ""

                if crawler_instance.platform == "wechat":
                    markdown = crawler_instance._inject_wechat_images(markdown, main_content)

                if not markdown or len(markdown) < 50:
                    body_text = await page.evaluate("() => document.body.innerText")
                    if body_text and len(body_text) > 100:
                        markdown = body_text

                if not markdown or len(markdown) < 50:
                    crawler_instance.error = "无法提取页面内容，可能需要登录或内容为空"
                    return

                crawler_instance.result = {
                    "status": "success",
                    "title": title,
                    "url": str(context.request.url),
                    "markdown": markdown,
                    "html": main_content,
                }

            except Exception as e:
                crawler_instance.error = str(e)

        try:
            await crawler.run([url])
        except Exception as e:
            self.error = str(e)

        if self.error:
            raise ValueError(self.error)

        if not self.result:
            raise ValueError("抓取失败，未能获取页面内容")

        return self.result


def process_images_in_markdown(markdown: str, html: str, base_url: str, output_dir: str) -> str:
    if not markdown:
        return markdown

    downloader = ImageDownloader(output_dir)

    try:
        img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        matches = re.findall(img_pattern, markdown)

        for alt_text, img_url in matches:
            if not img_url or img_url.startswith("data:"):
                continue

            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif not img_url.startswith("http"):
                img_url = urljoin(base_url, img_url)

            local_path = downloader.download_image(img_url)
            if local_path:
                markdown = markdown.replace(f"![{alt_text}]({img_url})", f"![{alt_text}]({local_path})")

        return markdown

    finally:
        downloader.close()


def format_markdown_content(markdown: str) -> str:
    if not markdown:
        return ""

    lines = markdown.split('\n')
    formatted_lines = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('```'):
            if in_code_block:
                formatted_lines.append('```')
                in_code_block = False
            else:
                in_code_block = True
                lang = stripped[3:].strip() or "text"
                formatted_lines.append(f"```{lang}")
        else:
            formatted_lines.append(line)

    result = '\n'.join(formatted_lines)
    result = result.replace('\n\n\n\n', '\n\n\n')

    return result.strip()


def save_article(title: str, url: str, markdown: str, html: str = "") -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    safe_title = sanitize_filename(title) or "untitled"
    filename = f"{today}_{safe_title}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    counter = 1
    while os.path.exists(filepath):
        filename = f"{today}_{safe_title}_{counter}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)
        counter += 1

    article_dir = os.path.dirname(filepath)
    markdown = process_images_in_markdown(markdown, html, url, article_dir)

    formatted_markdown = format_markdown_content(markdown)

    header = f"""---
title: {title}
url: {url}
date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
tags: [web-crawler]
---

# {title}

> 来源: [{url}]({url})

---

"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + formatted_markdown)

    return filepath


crawler = WebCrawler()


async def extract_url(url: str) -> dict[str, Any]:
    return await crawler.crawl(url)

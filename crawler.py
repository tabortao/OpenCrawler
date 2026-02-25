import asyncio
import hashlib
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
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

_executor = ThreadPoolExecutor(max_workers=4)


class ImageDownloader:
    def __init__(self, output_dir: str):
        self.images_dir = os.path.join(output_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        self.client = httpx.Client(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
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
            clean_url = url.replace("&amp;", "&")
            clean_url = clean_url.replace("&lt;", "<")
            clean_url = clean_url.replace("&gt;", ">")
            clean_url = clean_url.replace("&quot;", '"')
            
            if clean_url.startswith("//"):
                clean_url = "https:" + clean_url

            response = self.client.get(clean_url)
            if response.status_code != 200:
                return None

            content_type = response.headers.get("content-type", "")
            ext = self._get_image_extension(url, content_type)

            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            safe_hash = ''.join(c for c in url_hash if c.isalnum())
            filename = f"{safe_hash}{ext}"
            filepath = os.path.join(self.images_dir, filename)

            with open(filepath, "wb") as f:
                f.write(response.content)

            relative_path = f"images/{filename}"
            self.downloaded[url] = relative_path
            return relative_path

        except Exception as e:
            print(f"Failed to download image: {url[:50]}... Error: {e}")
            return None

    def close(self):
        self.client.close()


class WebCrawler:
    def _get_browser_args(self) -> dict[str, Any]:
        args: dict[str, Any] = {
            "headless": True,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-sync",
                "--disable-translate",
                "--disable-default-apps",
                "--mute-audio",
                "--no-first-run",
            ],
        }

        if PROXY_URL:
            args["proxy"] = {"server": PROXY_URL}

        return args

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

    def _check_login_status(self, page, platform: str) -> bool:
        if platform == "xiaohongshu":
            login_indicators = [
                '.login-container',
                '.login-btn',
                'text=登录后推荐更懂你的笔记',
                'text=手机号登录',
            ]
            for selector in login_indicators:
                try:
                    el = page.query_selector(selector)
                    if el and el.is_visible():
                        return False
                except Exception:
                    continue
            return True
        elif platform == "zhihu":
            try:
                login_text = page.query_selector('text=登录')
                if login_text and login_text.is_visible():
                    return False
            except Exception:
                pass
            return True
        return True

    def _scroll_page(self, page, times: int) -> None:
        if times <= 0:
            return

        for _ in range(times):
            try:
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                page.wait_for_timeout(400)
            except Exception:
                break

        try:
            page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass

    def _handle_zhihu_popup(self, page) -> None:
        close_selectors = [
            '.Modal-closeButton',
            'button[aria-label="关闭"]',
            '.CloseIcon',
        ]
        for sel in close_selectors:
            try:
                btn = page.query_selector(sel)
                if btn and btn.is_visible():
                    btn.click()
                    page.wait_for_timeout(300)
                    break
            except Exception:
                continue

    def _clean_zhihu_title(self, title: str) -> str:
        patterns = [
            r'\s*[\(（]\s*\d+\s*封私信.*?[\)）]',
            r'\s*[\(（]\s*\d+\s*条消息.*?[\)）]',
            r'\s*-\s*\d+\s*封私信.*',
            r'\s*\d+\s*封私信',
            r'\s*\d+\s*条消息',
        ]
        for pattern in patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        return title.strip()

    def _clean_zhihu_content(self, markdown: str) -> str:
        lines = markdown.split('\n')
        skip_patterns = [
            r'^关注\s*$',
            r'^推荐\s*$',
            r'^热榜\s*$',
            r'^专栏\s*$',
            r'^圈子\s*$',
            r'^New\s*$',
            r'^付费咨询\s*$',
            r'^知学堂\s*$',
            r'^直答\s*$',
            r'^消息\s*$',
            r'^私信\s*$',
            r'^创作中心\s*$',
            r'^\d+\s*$',
            r'^每天看网文\s*$',
            r'^​\s*$',
            r'^关注她\s*$',
            r'^关注他\s*$',
            r'^\d+\s*人赞同了该文章\s*$',
            r'^\d+\s*人赞同了该回答\s*$',
            r'^起点万订作者.*$',
            r'^雾野漫游\s*$',
            r'^RzJs\s*$',
        ]

        def is_nav_line(line: str) -> bool:
            stripped = line.strip()
            if not stripped:
                return False
            for pattern in skip_patterns:
                if re.match(pattern, stripped, re.IGNORECASE):
                    return True
            return False

        cleaned_lines = []
        prev_line = None
        for line in lines:
            stripped = line.strip()
            
            if is_nav_line(line):
                continue
            
            if stripped and stripped == prev_line:
                continue
            
            cleaned_lines.append(line)
            if stripped:
                prev_line = stripped

        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n{4,}', '\n\n\n', result)
        return result.strip()

    def _extract_main_content(self, page, platform: str) -> tuple[str, list[str]]:
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
        image_urls = []

        for selector in selectors:
            try:
                el = page.query_selector(selector)
                if el:
                    text = el.inner_text()
                    if len(text) > 100:
                        if platform == "wechat":
                            html = self._process_wechat_images(el)
                        else:
                            html = el.inner_html()

                        img_pattern = r'<img[^>]+(?:data-)?src=["\']([^"\']+)["\'][^>]*>'
                        image_urls = re.findall(img_pattern, html, re.IGNORECASE)
                        return html, image_urls
            except Exception:
                continue

        try:
            html = page.content()
            img_pattern = r'<img[^>]+(?:data-)?src=["\']([^"\']+)["\'][^>]*>'
            image_urls = re.findall(img_pattern, html, re.IGNORECASE)
            return html, image_urls
        except Exception:
            return "", []

    def _process_wechat_images(self, element) -> str:
        try:
            element.evaluate("""
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
            return element.inner_html()
        except Exception:
            return element.inner_html()

    def _extract_content_sync(self, url: str) -> dict[str, Any]:
        platform = detect_platform(url)
        config = get_platform_config(platform)

        with sync_playwright() as p:
            browser_args = self._get_browser_args()
            browser = p.chromium.launch(**browser_args)

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
                java_script_enabled=True,
                color_scheme="light",
                has_touch=False,
                is_mobile=False,
                ignore_https_errors=True,
            )

            xhs_cookies = self._get_cookies_for_platform("xiaohongshu")
            if xhs_cookies:
                context.add_cookies(xhs_cookies)

            zhihu_cookies = self._get_cookies_for_platform("zhihu")
            if zhihu_cookies:
                context.add_cookies(zhihu_cookies)

            page = context.new_page()
            page.set_default_timeout(45000)
            page.set_default_navigation_timeout(60000)

            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
                window.chrome = {
                    runtime: {}
                };
            """)

            try:
                if "xhslink.com" in url.lower():
                    page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3000)

                page.goto(url, wait_until="domcontentloaded", timeout=45000)

                final_url = page.url
                final_platform = detect_platform(final_url)
                
                if final_platform == "xiaohongshu":
                    page.wait_for_timeout(2000)
                    if not self._check_login_status(page, "xiaohongshu"):
                        print("Warning: 小红书未检测到登录状态，Cookie可能已过期")
                        page.reload(wait_until="networkidle", timeout=30000)
                        page.wait_for_timeout(2000)

                page.wait_for_load_state("domcontentloaded", timeout=20000)

                if platform == "zhihu" or final_platform == "zhihu":
                    page.wait_for_timeout(1500)
                    self._handle_zhihu_popup(page)
                    page.wait_for_timeout(500)

                self._scroll_page(page, config["scroll_times"])
                page.wait_for_timeout(500)

                html_content = page.content()
                title = extract_title_from_html(html_content)

                if platform == "zhihu":
                    title = self._clean_zhihu_title(title)

                main_content, image_urls = self._extract_main_content(page, platform)

                markdown = extract(main_content, include_links=True, include_images=True)
                markdown = clean_markdown(markdown) if markdown else ""

                if platform == "zhihu":
                    markdown = self._clean_zhihu_content(markdown)

                if not markdown or len(markdown) < 50:
                    body_text = page.evaluate("() => document.body.innerText")
                    if body_text and len(body_text) > 100:
                        markdown = body_text
                        if platform == "zhihu":
                            markdown = self._clean_zhihu_content(markdown)

                if not markdown or len(markdown) < 50:
                    raise ValueError("无法提取页面内容，可能需要登录或内容为空")

                return {
                    "status": "success",
                    "title": title,
                    "url": url,
                    "markdown": markdown,
                    "html": main_content,
                    "image_urls": image_urls,
                }

            finally:
                try:
                    browser.close()
                except Exception:
                    pass

    async def crawl(self, url: str) -> dict[str, Any]:
        platform = detect_platform(url)
        
        if platform == "xiaohongshu":
            from xhs_crawler import crawl_xiaohongshu
            try:
                result = await crawl_xiaohongshu(url, headless=True)
                return {
                    "status": "success",
                    "title": result["title"],
                    "url": result["url"],
                    "markdown": result["markdown"],
                    "html": "",
                    "image_urls": [],
                }
            except Exception as e:
                print(f"[WebCrawler] 小红书爬取失败，尝试通用方法: {e}")
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._extract_content_sync, url)


def html_to_markdown_with_images(html: str, image_urls: list[str], output_dir: str) -> str:
    if not html:
        return ""
    
    downloader = ImageDownloader(output_dir)
    
    try:
        img_counter = [0]
        
        def replace_data_src_img(match):
            full_tag = match.group(0)
            data_src = match.group(1)
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', full_tag, re.IGNORECASE)
            alt = alt_match.group(1) if alt_match else "图片"
            
            if not data_src or data_src.startswith("data:"):
                return ""
            
            clean_src = data_src.replace("&amp;", "&")
            local_path = downloader.download_image(clean_src)
            
            if local_path:
                img_counter[0] += 1
                return f'<p data-img-placeholder="true">IMG_PLACEHOLDER_{img_counter[0]}_{local_path}_{alt}</p>'
            return ""
        
        data_src_pattern = r'<img[^>]*data-src=["\']([^"\']+)["\'][^>]*>'
        html = re.sub(data_src_pattern, replace_data_src_img, html, flags=re.IGNORECASE)
        
        def replace_src_img(match):
            full_tag = match.group(0)
            src = match.group(1)
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', full_tag, re.IGNORECASE)
            alt = alt_match.group(1) if alt_match else "图片"
            
            if not src or src.startswith("data:"):
                return ""
            
            clean_src = src.replace("&amp;", "&")
            local_path = downloader.download_image(clean_src)
            
            if local_path:
                img_counter[0] += 1
                return f'<p data-img-placeholder="true">IMG_PLACEHOLDER_{img_counter[0]}_{local_path}_{alt}</p>'
            return ""
        
        src_pattern = r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>'
        html = re.sub(src_pattern, replace_src_img, html, flags=re.IGNORECASE)
        
        markdown = extract(html, include_links=True, include_images=True)
        markdown = clean_markdown(markdown) if markdown else ""
        
        if markdown:
            placeholder_pattern = r'IMG_PLACEHOLDER_(\d+)_([^_\s]+)_([^\n]+)'
            def restore_img(match):
                num = match.group(1)
                path = match.group(2)
                alt = match.group(3)
                return f"![{alt}]({path})"
            
            markdown = re.sub(placeholder_pattern, restore_img, markdown)
        
        return markdown
    finally:
        downloader.close()


def process_images_in_markdown(markdown: str, image_urls: list[str], output_dir: str) -> str:
    if not markdown and not image_urls:
        return markdown

    downloader = ImageDownloader(output_dir)

    try:
        img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        matches = re.findall(img_pattern, markdown)

        for alt_text, img_url in matches:
            if not img_url or img_url.startswith("data:"):
                continue

            clean_url = img_url.replace("&amp;", "&")
            local_path = downloader.download_image(clean_url)
            if local_path:
                markdown = markdown.replace(f"![{alt_text}]({img_url})", f"![{alt_text}]({local_path})")

        for i, img_url in enumerate(image_urls):
            if not img_url or img_url.startswith("data:"):
                continue

            img_url = img_url.replace("&amp;", "&")
            img_url = img_url.replace("&lt;", "<")
            img_url = img_url.replace("&gt;", ">")
            img_url = img_url.replace("&quot;", '"')

            if img_url in markdown:
                continue

            local_path = downloader.download_image(img_url)
            if local_path:
                markdown += f"\n\n![图片{i+1}]({local_path})"

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


def save_article(title: str, url: str, markdown: str, html: str = "", image_urls: list[str] = None, download_images: bool = False) -> str:
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

    if download_images and html:
        article_dir = os.path.dirname(filepath)
        article_images_dir = os.path.join(article_dir, "images")
        os.makedirs(article_images_dir, exist_ok=True)
        markdown = html_to_markdown_with_images(html, image_urls or [], article_dir)
    elif download_images:
        article_dir = os.path.dirname(filepath)
        article_images_dir = os.path.join(article_dir, "images")
        os.makedirs(article_images_dir, exist_ok=True)
        markdown = process_images_in_markdown(markdown, image_urls or [], article_dir)

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

import asyncio
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from playwright.sync_api import Browser, Page, sync_playwright
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


class WebCrawler:
    def __init__(self) -> None:
        self.browser: Browser | None = None

    def _get_browser_args(self) -> dict[str, Any]:
        args: dict[str, Any] = {
            "headless": True,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-dev-shm-usage",
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

    def _scroll_page(self, page: Page, times: int) -> None:
        if times <= 0:
            return

        for _ in range(times):
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            page.wait_for_timeout(500)

        page.evaluate("window.scrollTo(0, 0)")

    def _wait_for_selector(self, page: Page, selector: str, timeout: int) -> bool:
        selectors = selector.split(", ")
        for sel in selectors:
            try:
                page.wait_for_selector(sel.strip(), timeout=timeout)
                return True
            except Exception:
                continue
        return False

    def _clean_wechat_content(self, page: Page) -> None:
        page.evaluate("""
            const removeSelectors = [
                '.rich_media_tool',
                '.rich_media_area_extra',
                '.qr_code_pc',
                '#js_a_popular',
                '#js_cmt_area',
                '#js_sponsor',
                '.a_dialog_close'
            ];
            removeSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => el.remove());
            });
        """)

    def _handle_zhihu_popup(self, page: Page) -> None:
        try:
            close_btn = page.query_selector('.Modal-closeButton, .css-1e3y2ua')
            if close_btn:
                close_btn.click()
                page.wait_for_timeout(500)
        except Exception:
            pass

    def _extract_content_sync(self, url: str) -> dict[str, Any]:
        platform = detect_platform(url)
        config = get_platform_config(platform)

        with sync_playwright() as p:
            browser_args = self._get_browser_args()
            browser = p.chromium.launch(**browser_args)

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )

            cookies = self._get_cookies_for_platform(platform)
            if cookies:
                context.add_cookies(cookies)

            page = context.new_page()

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=config["timeout"])

                if platform == "zhihu":
                    self._handle_zhihu_popup(page)

                if config["selector"]:
                    self._wait_for_selector(page, config["selector"], config["timeout"])

                self._scroll_page(page, config["scroll_times"])

                if platform == "wechat":
                    self._clean_wechat_content(page)

                page.wait_for_timeout(1500)

                html_content = page.content()
                title = extract_title_from_html(html_content)

                main_content = self._extract_main_content(page, platform)

                markdown = extract(main_content, include_links=True, include_images=True)
                markdown = clean_markdown(markdown) if markdown else ""

                if not markdown or len(markdown) < 50:
                    raise ValueError("无法提取页面内容，可能需要登录或内容为空")

                return {
                    "status": "success",
                    "title": title,
                    "url": url,
                    "markdown": markdown,
                }

            finally:
                browser.close()

    def _extract_main_content(self, page: Page, platform: str) -> str:
        selectors_map = {
            "zhihu": [
                '.Post-RichText',
                '.RichText',
                '.RichContent-inner',
                '.RichContent',
                'article',
                '[itemprop="text"]',
                '.RichText ztext Post-RichText',
            ],
            "github": ['.markdown-body', 'article'],
            "xiaohongshu": ['.note-content', '#detail-desc', '.content'],
            "wechat": ['.rich_media_content', '#js_content'],
            "generic": ['article', '.content', '.post', 'main', '.article-body'],
        }

        selectors = selectors_map.get(platform, selectors_map["generic"])

        for selector in selectors:
            try:
                el = page.query_selector(selector)
                if el:
                    text = el.inner_text()
                    if len(text) > 100:
                        return el.inner_html()
            except Exception:
                continue

        return page.content()

    async def extract_content(self, url: str) -> dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._extract_content_sync, url)


def save_article(title: str, url: str, markdown: str) -> str:
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

    header = f"""---
title: {title}
url: {url}
date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
---

"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + markdown)

    return filepath


crawler = WebCrawler()


async def extract_url(url: str) -> dict[str, Any]:
    return await crawler.extract_content(url)

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

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
            'button.Button.Modal-closeButton',
            '[class*="Modal"] button[aria-label*="关闭"]',
            'button[class*="close"]',
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
            )

            cookies = self._get_cookies_for_platform(platform)
            if cookies:
                context.add_cookies(cookies)

            page = context.new_page()
            page.set_default_timeout(45000)
            page.set_default_navigation_timeout(60000)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)

                page.wait_for_load_state("domcontentloaded", timeout=20000)

                if platform == "zhihu":
                    page.wait_for_timeout(2000)
                    self._handle_zhihu_popup(page)
                    page.wait_for_timeout(1000)

                self._scroll_page(page, config["scroll_times"])
                page.wait_for_timeout(800)

                html_content = page.content()
                title = extract_title_from_html(html_content)

                main_content = self._extract_main_content(page, platform)

                markdown = extract(main_content, include_links=True, include_images=True)
                markdown = clean_markdown(markdown) if markdown else ""

                if not markdown or len(markdown) < 50:
                    body_text = page.evaluate("() => document.body.innerText")
                    if body_text and len(body_text) > 100:
                        markdown = body_text

                if not markdown or len(markdown) < 50:
                    raise ValueError("无法提取页面内容，可能需要登录或内容为空")

                return {
                    "status": "success",
                    "title": title,
                    "url": url,
                    "markdown": markdown,
                }

            finally:
                try:
                    browser.close()
                except Exception:
                    pass

    def _extract_main_content(self, page, platform: str) -> str:
        selectors_map = {
            "zhihu": [
                '.Post-RichTextContainer',
                '.Post-RichText',
                '.RichText',
                '.RichContent-inner',
                '.RichContent',
                'article',
                '.ztext',
                '[itemprop="text"]',
                '.RichText.ztext',
            ],
            "github": ['.markdown-body', 'article', '.readme'],
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

        try:
            return page.content()
        except Exception:
            return ""

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

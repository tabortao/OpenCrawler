"""
少数派爬虫插件

支持少数派文章内容的提取
"""

import re
from typing import Any

from app.plugins.base import BasePlugin, PluginInfo
from app.crawlers.base import CrawlResult, BaseCrawler
from app.utils.text import extract_title_from_html
from app.converters.markdown import MarkdownConverter
from app.converters.image_extractor import ImageExtractor


class SspaiCrawler(BaseCrawler):
    """少数派平台爬虫"""
    
    @property
    def name(self) -> str:
        return "sspai"
    
    @property
    def platforms(self) -> list[str]:
        return ["sspai"]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """提取少数派文章内容"""
        from playwright.async_api import async_playwright
        
        config = self.get_platform_config("sspai")
        
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(**self.get_browser_args())
        
        self._context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        
        page = await self._context.new_page()
        page.set_default_timeout(config.timeout)
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=config.timeout)
            await page.wait_for_load_state("domcontentloaded", timeout=config.timeout)
            
            for _ in range(config.scroll_times):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(400)
            
            try:
                await page.evaluate("window.scrollTo(0, 0)")
            except Exception:
                pass
            
            html_content = await page.content()
            title = extract_title_from_html(html_content)
            
            if title.endswith(" - 少数派"):
                title = title[:-6].strip()
            
            main_html = await self._extract_main_content(page)
            image_urls = ImageExtractor.extract_from_html(main_html)
            
            markdown = MarkdownConverter.convert_html_to_markdown(main_html, platform="sspai")
            
            if not markdown or len(markdown) < 50:
                body_text = await page.evaluate("() => document.body.innerText")
                if body_text and len(body_text) > 100:
                    markdown = body_text
            
            return CrawlResult(
                title=title,
                url=url,
                markdown=markdown,
                html=main_html,
                image_urls=image_urls,
            )
        
        finally:
            await self.close()
    
    async def _extract_main_content(self, page) -> str:
        """提取主要内容"""
        selectors = ["article", ".article-content", ".content"]
        
        for selector in selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    text = await el.inner_text()
                    if len(text) > 100:
                        return await el.inner_html()
            except Exception:
                continue
        
        return await page.content()


class SspaiPlugin(BasePlugin):
    """少数派平台插件"""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="sspai",
            version="1.0.0",
            description="少数派文章内容提取插件",
            author="MyCrawler",
            platforms=["sspai"],
        )
    
    @property
    def platforms(self) -> list[str]:
        return ["sspai"]
    
    def get_supported_url_patterns(self) -> list[str]:
        return [
            r"https?://sspai\.com/post/\d+",
            r"https?://www\.sspai\.com/post/\d+",
        ]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """提取少数派文章内容"""
        crawler = SspaiCrawler()
        return await crawler.extract(url, **kwargs)

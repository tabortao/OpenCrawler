"""
通用插件

处理未定义的通用类型网站
"""

import re
from typing import Any, Optional

from app.plugins.base import BasePlugin, PluginInfo
from app.crawlers.base import CrawlResult, BaseCrawler
from app.utils.text import extract_title_from_html
from app.converters.markdown import MarkdownConverter
from app.converters.image_extractor import ImageExtractor


class GenericCrawler(BaseCrawler):
    """通用平台爬虫"""
    
    @property
    def name(self) -> str:
        return "generic"
    
    @property
    def platforms(self) -> list[str]:
        return ["generic"]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """
        使用通用方法提取页面内容
        
        Args:
            url: 目标 URL
            **kwargs: 额外参数
        
        Returns:
            爬取结果
        """
        from playwright.async_api import async_playwright
        from app.utils.url import detect_platform
        
        platform = detect_platform(url)
        config = self.get_platform_config(platform)
        
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(**self.get_browser_args())
        
        self._context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        
        page = await self._context.new_page()
        page.set_default_timeout(self.settings.browser_timeout)
        page.set_default_navigation_timeout(self.settings.browser_navigation_timeout)
        
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
            window.chrome = { runtime: {} };
        """)
        
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
            
            main_html = await self._extract_main_content(page)
            image_urls = ImageExtractor.extract_from_html(main_html)
            
            markdown = MarkdownConverter.convert_html_to_markdown(main_html, platform="generic")
            
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
    
    async def _extract_main_content(self, page, platform: str = "generic") -> str:
        """
        提取主要内容
        
        尝试多种选择器策略来提取主要内容
        
        Args:
            page: Playwright 页面对象
            platform: 平台名称
        
        Returns:
            主要内容的 HTML
        """
        selectors = [
            "article",
            ".article-content",
            ".post-content",
            ".entry-content",
            ".content",
            ".post",
            "main",
            "#content",
            "#main",
            ".main-content",
        ]
        
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


class GenericPlugin(BasePlugin):
    """通用平台插件"""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="generic",
            version="1.0.0",
            description="通用网站内容提取插件，处理未定义的网站类型",
            author="OpenCrawler",
            platforms=["generic"],
        )
    
    @property
    def platforms(self) -> list[str]:
        return ["generic"]
    
    def get_supported_url_patterns(self) -> list[str]:
        """支持所有 HTTP/HTTPS URL"""
        return [
            r"https?://.*",
        ]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """提取页面内容"""
        crawler = GenericCrawler()
        return await crawler.extract(url, **kwargs)

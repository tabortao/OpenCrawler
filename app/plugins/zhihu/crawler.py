"""
知乎爬虫插件

支持知乎文章、回答等内容的提取
"""

import re
from typing import Any

from app.plugins.base import BasePlugin, PluginInfo
from app.crawlers.base import CrawlResult, BaseCrawler
from app.core.exceptions import AuthenticationError, ContentExtractionError
from app.utils.text import extract_title_from_html, clean_zhihu_title
from app.utils.url import parse_cookie_string
from app.converters.markdown import MarkdownConverter
from app.converters.image_extractor import ImageExtractor


class ZhihuCrawler(BaseCrawler):
    """知乎平台爬虫"""
    
    @property
    def name(self) -> str:
        return "zhihu"
    
    @property
    def platforms(self) -> list[str]:
        return ["zhihu"]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """提取知乎页面内容"""
        from playwright.async_api import async_playwright
        
        config = self.get_platform_config("zhihu")
        
        if not self.settings.zhihu_cookie:
            raise AuthenticationError(
                message="知乎平台需要登录，请配置 ZHIHU_COOKIE",
                platform="zhihu",
            )
        
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(**self.get_browser_args())
        
        self._context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        
        cookies = parse_cookie_string(self.settings.zhihu_cookie)
        for cookie in cookies:
            cookie["domain"] = ".zhihu.com"
        await self._context.add_cookies(cookies)
        
        page = await self._context.new_page()
        page.set_default_timeout(config.timeout)
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=config.timeout)
            await page.wait_for_load_state("domcontentloaded", timeout=config.timeout)
            await page.wait_for_timeout(1500)
            
            await self._handle_popup(page)
            
            for _ in range(config.scroll_times):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(400)
            
            try:
                await page.evaluate("window.scrollTo(0, 0)")
            except Exception:
                pass
            
            html_content = await page.content()
            title = extract_title_from_html(html_content)
            title = clean_zhihu_title(title)
            
            if self._is_cookie_expired(html_content, title):
                raise AuthenticationError(
                    message="知乎 Cookie 已过期，请更新 Cookie",
                    platform="zhihu",
                )
            
            main_html = await self._extract_main_content(page)
            image_urls = ImageExtractor.extract_from_html(main_html)
            
            markdown = MarkdownConverter.convert_html_to_markdown(main_html, platform="zhihu")
            markdown = self._clean_content(markdown)
            
            if not markdown or len(markdown) < 50:
                body_text = await page.evaluate("() => document.body.innerText")
                if body_text and len(body_text) > 100:
                    markdown = self._clean_content(body_text)
            
            if not markdown or len(markdown) < 50:
                raise ContentExtractionError(
                    message="无法提取页面内容，可能需要登录或内容为空",
                    url=url,
                    platform="zhihu",
                )
            
            return CrawlResult(
                title=title,
                url=url,
                markdown=markdown,
                html=main_html,
                image_urls=image_urls,
            )
        
        finally:
            await self.close()
    
    async def _handle_popup(self, page) -> None:
        """处理知乎弹窗"""
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
                        await page.wait_for_timeout(300)
                        break
            except Exception:
                continue
    
    async def _extract_main_content(self, page) -> str:
        """提取主要内容"""
        selectors = [
            '.Post-RichTextContainer',
            '.Post-RichText',
            '.RichText',
            '.RichContent-inner',
            'article',
            '.ztext',
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
    
    def _is_cookie_expired(self, html: str, title: str) -> bool:
        """检测知乎 Cookie 是否过期"""
        expired_indicators = [
            "你似乎来到了没有知识存在的荒原",
            "登录知乎",
            "注册知乎",
            "安全验证",
            "请验证您的身份",
        ]
        
        for indicator in expired_indicators:
            if indicator in html or indicator in title:
                return True
        
        return False
    
    def _clean_content(self, markdown: str) -> str:
        """清理知乎内容"""
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


class ZhihuPlugin(BasePlugin):
    """知乎平台插件"""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="zhihu",
            version="1.0.0",
            description="知乎文章、回答内容提取插件",
            author="MyCrawler",
            platforms=["zhihu"],
        )
    
    @property
    def platforms(self) -> list[str]:
        return ["zhihu"]
    
    def get_supported_url_patterns(self) -> list[str]:
        return [
            r"https?://zhuanlan\.zhihu\.com/p/\d+",
            r"https?://www\.zhihu\.com/question/\d+/answer/\d+",
            r"https?://www\.zhihu\.com/question/\d+",
        ]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """提取知乎页面内容"""
        crawler = ZhihuCrawler()
        return await crawler.extract(url, **kwargs)

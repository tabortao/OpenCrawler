"""
微信公众号爬虫插件

支持微信公众号文章内容的提取
"""

import re
from typing import Any

from app.plugins.base import BasePlugin, PluginInfo
from app.crawlers.base import CrawlResult, BaseCrawler
from app.utils.text import extract_title_from_html
from app.converters.markdown import MarkdownConverter
from app.converters.image_extractor import ImageExtractor


class WeChatCrawler(BaseCrawler):
    """微信公众号平台爬虫"""
    
    @property
    def name(self) -> str:
        return "wechat"
    
    @property
    def platforms(self) -> list[str]:
        return ["wechat"]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """提取微信公众号文章内容"""
        from playwright.async_api import async_playwright
        
        config = self.get_platform_config("wechat")
        
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
            
            main_html = await self._extract_main_content(page)
            image_urls = ImageExtractor.extract_from_html(main_html)
            
            markdown = MarkdownConverter.convert_html_to_markdown(main_html, platform="wechat")
            markdown = self._clean_content(markdown)
            
            if not markdown or len(markdown) < 50:
                body_text = await page.evaluate("() => document.body.innerText")
                if body_text and len(body_text) > 100:
                    markdown = self._clean_content(body_text)
            
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
        selectors = [".rich_media_content", "#js_content"]
        
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
    
    def _clean_content(self, markdown: str) -> str:
        """清理微信公众号内容"""
        lines = markdown.split('\n')
        
        skip_patterns = [
            r'^S 全屏播放',
            r'^full_screen_mv',
            r'^已关注',
            r'^关注\s*$',
            r'^重播',
            r'^分享\s*$',
            r'^点赞后',
            r'^赞\s*$',
            r'^随便看看',
            r'^有拓展内容',
            r'^广告内容',
            r'^关闭\*\*观看更多\*\*',
            r'^更多\s*$',
            r'^\*退出全屏',
            r'^\*切换到竖屏全屏',
            r'^\*全屏\*',
            r'^\d+/\d+$',
            r'^\d+:\d+/\d+:\d+',
            r'^切换到横屏模式',
            r'^继续播放',
            r'^进度条',
            r'^播放',
            r'^倍速',
            r'^超清流畅',
            r'^您的浏览器不支持',
            r'^继续观看',
            r'^观看更多',
            r'^原创',
            r'^已同步到看一看',
            r'^写下你的评论',
            r'^E 视频播放器',
            r'^S 视频社交',
            r'^视频详情',
            r'^分享点赞在看',
            r'^0/0$',
            r'^00:00/',
            r'^倍速播放中',
        ]
        
        def is_skip_line(line: str) -> bool:
            stripped = line.strip()
            if not stripped:
                return False
            for pattern in skip_patterns:
                if re.match(pattern, stripped):
                    return True
            if re.match(r'^\d+:\d+/\d+:\d+', stripped):
                return True
            if re.match(r'^\d+/\d+$', stripped):
                return True
            return False
        
        cleaned_lines = []
        prev_line = None
        
        for line in lines:
            stripped = line.strip()
            
            if is_skip_line(line):
                continue
            
            if stripped and stripped == prev_line:
                continue
            
            if '<span class=' in stripped:
                continue
            
            cleaned_lines.append(line)
            if stripped:
                prev_line = stripped
        
        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n{4,}', '\n\n\n', result)
        
        return result.strip()


class WeChatPlugin(BasePlugin):
    """微信公众号平台插件"""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="wechat",
            version="1.0.0",
            description="微信公众号文章内容提取插件",
            author="MyCrawler",
            platforms=["wechat"],
        )
    
    @property
    def platforms(self) -> list[str]:
        return ["wechat"]
    
    def get_supported_url_patterns(self) -> list[str]:
        return [
            r"https?://mp\.weixin\.qq\.com/s/[a-zA-Z0-9_-]+",
        ]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """提取微信公众号文章内容"""
        crawler = WeChatCrawler()
        return await crawler.extract(url, **kwargs)

"""
今日头条爬虫插件

支持今日头条文章内容的提取
"""

import re
from typing import Any

from app.plugins.base import BasePlugin, PluginInfo
from app.crawlers.base import CrawlResult, BaseCrawler
from app.core.exceptions import ContentExtractionError
from app.utils.text import extract_title_from_html
from app.converters.markdown import MarkdownConverter
from app.converters.image_extractor import ImageExtractor


class ToutiaoCrawler(BaseCrawler):
    """今日头条平台爬虫"""
    
    @property
    def name(self) -> str:
        return "toutiao"
    
    @property
    def platforms(self) -> list[str]:
        return ["toutiao"]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """提取今日头条页面内容"""
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        
        config = self.get_platform_config("toutiao")
        
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(**self.get_browser_args())
        
        self._context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            # 禁用重定向，避免执行上下文被销毁
            java_script_enabled=True,
        )
        
        page = await self._context.new_page()
        page.set_default_timeout(config.timeout)
        
        # 监听页面导航，防止意外重定向
        navigation_events = []
        async def on_navigation(url):
            navigation_events.append(url)
        
        page.on("framenavigated", lambda frame: on_navigation(frame.url))
        
        try:
            # 导航到页面
            await page.goto(url, wait_until="networkidle", timeout=config.timeout)
            
            # 等待页面稳定
            await page.wait_for_timeout(3000)
            
            # 处理弹窗
            await self._handle_popup(page)
            
            # 滚动页面加载内容（多次滚动以确保所有图片都加载）
            for _ in range(config.scroll_times * 2):
                try:
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(600)
                except Exception:
                    break
            
            # 滚动到顶部
            try:
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(1000)
            except Exception:
                pass
            
            # 再次滚动到底部，确保所有内容都加载
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
            except Exception:
                pass
            
            # 获取页面内容
            html_content = await page.content()
            title = extract_title_from_html(html_content)
            title = self._clean_title(title)
            
            # 提取主要内容
            main_html = await self._extract_main_content(page)
            image_urls = ImageExtractor.extract_from_html(main_html)
            
            # 转换为 Markdown
            markdown = MarkdownConverter.convert_html_to_markdown(main_html, platform="toutiao")
            markdown = self._clean_content(markdown)
            
            # 备用方案：如果 Markdown 内容太少，尝试提取纯文本
            if not markdown or len(markdown) < 50:
                try:
                    body_text = await page.evaluate("() => document.body.innerText")
                    if body_text and len(body_text) > 100:
                        markdown = self._clean_content(body_text)
                except Exception:
                    pass
            
            # 检查内容是否有效
            if not markdown or len(markdown) < 50:
                raise ContentExtractionError(
                    message="无法提取页面内容，可能需要登录或内容为空",
                    url=url,
                    platform="toutiao",
                )
            
            return CrawlResult(
                title=title,
                url=url,
                markdown=markdown,
                html=main_html,
                image_urls=image_urls,
            )
        
        except PlaywrightTimeoutError:
            # 处理超时错误
            html_content = await page.content()
            title = extract_title_from_html(html_content)
            title = self._clean_title(title)
            main_html = await self._extract_main_content(page)
            
            if main_html:
                markdown = MarkdownConverter.convert_html_to_markdown(main_html, platform="toutiao")
                markdown = self._clean_content(markdown)
                
                if markdown and len(markdown) >= 50:
                    image_urls = ImageExtractor.extract_from_html(main_html)
                    return CrawlResult(
                        title=title,
                        url=url,
                        markdown=markdown,
                        html=main_html,
                        image_urls=image_urls,
                    )
            
            raise ContentExtractionError(
                message="页面加载超时，无法提取完整内容",
                url=url,
                platform="toutiao",
            )
        
        finally:
            await self.close()
    
    async def _handle_popup(self, page) -> None:
        """处理今日头条弹窗"""
        close_selectors = [
            '.close-btn',
            '.btn-close',
            '.close',
            'button[aria-label="关闭"]',
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
            '.article-content',
            '.content',
            'article',
            '.content-wrapper',
            '.article-main',
        ]
        
        for selector in selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    text = await el.inner_text()
                    if len(text) > 100:
                        # 获取完整的 HTML 内容，包含图片的完整 URL
                        html = await el.inner_html()
                        return html
            except Exception:
                continue
        
        return await page.content()
    
    def _clean_title(self, title: str) -> str:
        """清理标题"""
        # 移除标题中的无关内容
        title = re.sub(r'\s*-\s*今日头条', '', title)
        title = re.sub(r'\s*_\s*今日头条', '', title)
        return title.strip()
    
    def _clean_content(self, markdown: str) -> str:
        """清理内容"""
        lines = markdown.split('\n')
        skip_patterns = [
            r'^关注\s*$',
            r'^推荐\s*$',
            r'^热榜\s*$',
            r'^头条\s*$',
            r'^抖音\s*$',
            r'^西瓜视频\s*$',
            r'^火山小视频\s*$',
            r'^悟空问答\s*$',
            r'^微头条\s*$',
            r'^New\s*$',
            r'^\d+\s*$',
            r'^​\s*$',
            r'^相关阅读\s*$',
            r'^热门评论\s*$',
            r'^广告\s*$',
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


class ToutiaoPlugin(BasePlugin):
    """今日头条平台插件"""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="toutiao",
            version="1.0.0",
            description="今日头条文章内容提取插件",
            author="MyCrawler",
            platforms=["toutiao"],
        )
    
    @property
    def platforms(self) -> list[str]:
        return ["toutiao"]
    
    def get_supported_url_patterns(self) -> list[str]:
        return [
            r"https?://www\.toutiao\.com/article/\d+",
            r"https?://toutiao\.com/article/\d+",
        ]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """提取今日头条页面内容"""
        crawler = ToutiaoCrawler()
        return await crawler.extract(url, **kwargs)
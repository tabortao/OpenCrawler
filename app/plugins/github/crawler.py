"""
GitHub 爬虫插件

支持 GitHub 仓库 README 等内容的提取
"""

import re
from typing import Any
from urllib.parse import urljoin, urlparse

from app.plugins.base import BasePlugin, PluginInfo
from app.crawlers.base import CrawlResult, BaseCrawler
from app.utils.text import extract_title_from_html
from app.converters.markdown import MarkdownConverter
from app.converters.image_extractor import ImageExtractor


class GitHubCrawler(BaseCrawler):
    """GitHub 平台爬虫"""
    
    @property
    def name(self) -> str:
        return "github"
    
    @property
    def platforms(self) -> list[str]:
        return ["github"]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """提取 GitHub 页面内容"""
        from playwright.async_api import async_playwright
        
        config = self.get_platform_config("github")
        
        title = self._extract_project_name(url)
        
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(**self.get_browser_args())
        
        self._context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        
        page = await self._context.new_page()
        page.set_default_timeout(config.timeout)
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=config.timeout)
            await page.wait_for_load_state("domcontentloaded", timeout=config.timeout)
            
            main_html = await self._extract_readme(page)
            
            main_html = self._fix_github_image_urls(main_html, url)
            
            image_urls = ImageExtractor.extract_from_html(main_html)
            
            markdown = MarkdownConverter.convert_html_to_markdown(main_html, platform="github")
            
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
    
    def _extract_project_name(self, url: str) -> str:
        """
        从 URL 中提取项目名称
        
        Args:
            url: GitHub 仓库 URL
        
        Returns:
            项目名称（格式：owner/repo）
        """
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        parts = path.split('/')
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1]
            
            if repo.endswith('.git'):
                repo = repo[:-4]
            
            return f"{owner}/{repo}"
        
        return "GitHub Project"
    
    def _fix_github_image_urls(self, html: str, base_url: str) -> str:
        """
        修复 GitHub 图片 URL
        
        处理以下情况：
        1. 相对路径转换为完整 URL
        2. GitHub raw 图片链接
        3. GitHub 用户内容链接
        
        Args:
            html: HTML 内容
            base_url: 基础 URL
        
        Returns:
            修复后的 HTML
        """
        parsed = urlparse(base_url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1]
            branch = "main"
            
            if len(path_parts) >= 4 and path_parts[2] in ['blob', 'tree']:
                branch = path_parts[3]
        else:
            owner = ""
            repo = ""
            branch = "main"
        
        def replace_img_src(match):
            full_match = match.group(0)
            src = match.group(1)
            
            if src.startswith('data:'):
                return full_match
            
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                if owner and repo:
                    src = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}{src}"
                else:
                    src = f"https://github.com{src}"
            elif not src.startswith('http'):
                if owner and repo:
                    base_raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}"
                    src = urljoin(base_raw_url + '/', src)
                else:
                    src = urljoin(base_url, src)
            
            if 'github.com' in src and '/blob/' in src:
                src = src.replace('github.com', 'raw.githubusercontent.com')
                src = src.replace('/blob/', '/')
            
            if 'camo.githubusercontent.com' in src:
                pass
            
            return f'src="{src}"'
        
        html = re.sub(r'src="([^"]+)"', replace_img_src, html)
        
        def replace_href(match):
            full_match = match.group(0)
            href = match.group(1)
            
            if href.startswith('http') or href.startswith('#') or href.startswith('mailto:'):
                return full_match
            
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = f"https://github.com{href}"
            else:
                href = urljoin(base_url, href)
            
            return f'href="{href}"'
        
        return html
    
    async def _extract_readme(self, page) -> str:
        """提取 README 内容"""
        selectors = [".markdown-body", "article.markdown-body", ".readme"]
        
        for selector in selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    text = await el.inner_text()
                    if len(text) > 50:
                        return await el.inner_html()
            except Exception:
                continue
        
        return await page.content()


class GitHubPlugin(BasePlugin):
    """GitHub 平台插件"""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="github",
            version="1.0.0",
            description="GitHub 仓库内容提取插件",
            author="OpenCrawler",
            platforms=["github"],
        )
    
    @property
    def platforms(self) -> list[str]:
        return ["github"]
    
    def get_supported_url_patterns(self) -> list[str]:
        return [
            r"https?://github\.com/[\w-]+/[\w.-]+",
            r"https?://github\.com/[\w-]+/[\w.-]+/blob/.*",
            r"https?://github\.com/[\w-]+/[\w.-]+/tree/.*",
        ]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """提取 GitHub 页面内容"""
        crawler = GitHubCrawler()
        return await crawler.extract(url, **kwargs)

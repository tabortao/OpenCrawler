"""
通用插件

处理未定义的通用类型网站，提供智能内容提取能力
"""

import re
from typing import Any, Optional, Tuple
from dataclasses import dataclass

from app.plugins.base import BasePlugin, PluginInfo
from app.crawlers.base import CrawlResult, BaseCrawler
from app.utils.text import extract_title_from_html
from app.converters.markdown import MarkdownConverter
from app.converters.image_extractor import ImageExtractor


@dataclass
class ContentCandidate:
    """内容候选数据类"""
    html: str
    text_length: int
    selector: str
    score: float


class GenericCrawler(BaseCrawler):
    """通用平台爬虫，支持智能内容提取"""
    
    PRIMARY_CONTENT_SELECTORS = [
        ("article", 100),
        ("[role='main']", 95),
        (".rich_media_content", 95),
        ("#js_content", 95),
        (".post-content", 90),
        (".article-content", 90),
        (".entry-content", 90),
        (".content-body", 85),
        (".article-body", 85),
        (".post-body", 85),
        (".story-body", 85),
        (".blog-content", 80),
        (".post-text", 80),
        (".main-content", 80),
        (".page-content", 75),
        (".single-content", 75),
        (".post-entry", 75),
        (".text-content", 70),
        (".article__content", 70),
        (".post__content", 70),
        (".content", 65),
        (".post", 60),
        ("main", 55),
        ("#content", 50),
        ("#main", 50),
        ("#article", 50),
    ]
    
    REMOVE_SELECTORS = [
        "nav", "header", "footer", "aside",
        ".sidebar", ".navigation", ".nav", ".menu",
        ".comments", ".comment", ".comment-list",
        ".related", ".recommended", ".recommend",
        ".advertisement", ".ad", ".ads", ".ad-container",
        ".social-share", ".share-buttons", ".social",
        ".author-bio", ".author-info", ".author-card",
        ".tags", ".tag-list", ".post-tags",
        ".breadcrumb", ".pagination",
        ".newsletter", ".subscribe", ".popup", ".modal",
        ".cookie-banner", ".gdpr", ".privacy",
        ".related-posts", ".related-articles",
        ".popular-posts", ".trending",
        ".widget", ".sidebar-widget",
        "[class*='sidebar']", "[class*='footer-']",
        "[class*='header-']:not([class*='header-content'])",
        "[class*='nav-']:not([class*='nav-content'])",
        "[class*='ad-']", "[class*='ads-']",
        "[class*='social-']", "[class*='share-']",
        "[id*='sidebar']", "[id*='footer']",
        "[id*='header']:not([id*='header-content'])",
        "[id*='nav-']:not([id*='nav-content'])",
        "[id*='ad-']", "[id*='ads-']",
    ]
    
    TITLE_SELECTORS = [
        'meta[property="og:title"]',
        'meta[name="twitter:title"]',
        'meta[name="title"]',
        'meta[itemprop="headline"]',
        '#activity-name',
        '.article-title',
        '.post-title',
        '.entry-title',
        '.page-title',
        'h1.title',
        'h1',
        'title',
    ]
    
    SKIP_CONTENT_PATTERNS = [
        r'^本文使用\s*',
        r'^首发于\s*',
        r'^作者\s*',
        r'^联系方式\s*',
        r'^微信公众号\s*',
        r'^扫码关注\s*',
        r'^分享到\s*',
        r'^点赞\s*$',
        r'^收藏\s*$',
        r'^评论\s*$',
        r'^更多精彩内容\s*',
        r'^相关推荐\s*',
        r'^热门文章\s*',
        r'^往期精选\s*',
        r'^广告\s*$',
        r'^展开全文\s*',
        r'^收起\s*$',
        r'^已编辑\s*$',
        r'^修改于\s*',
        r'^\d+人赞同了该文章',
        r'^\d+人收藏',
        r'^\d+人点赞',
        r'^\d+人阅读',
        r'^阅读原文',
        r'^查看原文',
        r'^原文链接',
        r'^点击查看',
        r'^点击阅读',
        r'^关注公众号',
        r'^长按识别',
        r'^微信扫码',
        r'^赞赏\s*$',
        r'^打赏\s*$',
        r'^喜欢\s*$',
        r'^分享\s*$',
        r'^转发\s*$',
        r'^S 全屏播放',
        r'^full_screen_mv',
        r'^已关注',
        r'^关注\s*$',
        r'^重播',
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
    
    @property
    def name(self) -> str:
        return "generic"
    
    @property
    def platforms(self) -> list[str]:
        return ["generic"]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """
        使用智能方法提取页面内容
        
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
        
        await self._inject_stealth_scripts(page)
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=config.timeout)
            await page.wait_for_load_state("domcontentloaded", timeout=config.timeout)
            
            await self._wait_for_dynamic_content(page)
            
            for i in range(config.scroll_times):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(500)
                if i % 2 == 1:
                    await self._wait_for_lazy_images(page)
            
            try:
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(300)
            except Exception:
                pass
            
            html_content = await page.content()
            title = self._extract_title(html_content, page)
            
            main_html = await self._extract_main_content_smart(page, html_content)
            image_urls = ImageExtractor.extract_from_html(main_html)
            
            markdown = MarkdownConverter.convert_html_to_markdown(main_html, platform="generic")
            markdown = self._clean_content(markdown)
            
            if not markdown or len(markdown) < 100:
                markdown = self._extract_with_trafilatura(html_content)
            
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
    
    async def _inject_stealth_scripts(self, page) -> None:
        """注入反检测脚本"""
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
            
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({ state: 'granted' })
                })
            });
        """)
    
    async def _wait_for_dynamic_content(self, page, max_wait: int = 3000) -> None:
        """等待动态内容加载"""
        try:
            await page.wait_for_function("""
                () => {
                    const article = document.querySelector('article, [role="main"], .content, main');
                    if (article && article.innerText.length > 200) {
                        return true;
                    }
                    const body = document.body;
                    return body.innerText.length > 500;
                }
            """, timeout=max_wait)
        except Exception:
            pass
    
    def _extract_title(self, html_content: str, page) -> str:
        """
        智能提取页面标题
        
        优先级：
        1. Open Graph 标签
        2. Twitter 标签
        3. Schema.org 标签
        4. 特定元素 ID
        5. H1 标签
        6. Title 标签
        """
        title = extract_title_from_html(html_content)
        
        if not title:
            title = self._extract_title_from_page(page)
        
        title = self._clean_title(title)
        
        return title
    
    async def _extract_title_from_page(self, page) -> str:
        """从页面元素中提取标题"""
        for selector in self.TITLE_SELECTORS:
            try:
                if selector.startswith('meta'):
                    el = await page.query_selector(selector)
                    if el:
                        content = await el.get_attribute('content')
                        if content:
                            return content.strip()
                else:
                    el = await page.query_selector(selector)
                    if el:
                        text = await el.inner_text()
                        if text and len(text.strip()) > 2:
                            return text.strip()
            except Exception:
                continue
        return ""
    
    def _clean_title(self, title: str) -> str:
        """清理标题"""
        if not title:
            return ""
        
        title = re.sub(r'\s+', ' ', title)
        
        suffixes = [
            " - 知乎", " - 少数派", " - 微信公众号",
            " - 小红书", " - 掘金", " - CSDN", " - 简书",
            " - 博客园", " - 思否", " - 今日头条",
            " - SegmentFault", " - Stack Overflow",
            " - Reddit", " - 网易新闻", " - 搜狐新闻",
            " _ 知乎", " | 知乎", " | 少数派",
            " _ 新浪博客", " - 微信公众平台",
        ]
        
        for suffix in suffixes:
            if title.endswith(suffix):
                title = title[:-len(suffix)].strip()
        
        title = re.sub(r'\s*[-_|]\s*[^-_|]+\s*$', '', title)
        
        patterns = [
            r'\s*[\(（]\s*\d+\s*封私信.*?[\)）]',
            r'\s*[\(（]\s*\d+\s*条消息.*?[\)）]',
            r'\s*-\s*\d+\s*封私信.*',
        ]
        
        for pattern in patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        return title.strip()
    
    async def _wait_for_lazy_images(self, page) -> None:
        """等待懒加载图片加载完成"""
        try:
            await page.evaluate("""
                () => {
                    const images = document.querySelectorAll('img[data-src], img[data-original], img[data-lazy-src], img[data-lazy], img[loading="lazy"]');
                    images.forEach(img => {
                        const src = img.dataset.src || img.dataset.original || img.dataset.lazySrc || img.dataset.lazy;
                        if (src && !img.src.includes(src.split('?')[0])) {
                            img.src = src;
                        }
                        img.loading = 'eager';
                    });
                    
                    const pictureSources = document.querySelectorAll('source[data-srcset], source[data-src]');
                    pictureSources.forEach(source => {
                        const srcset = source.dataset.srcset || source.dataset.src;
                        if (srcset) {
                            source.srcset = srcset;
                        }
                    });
                }
            """)
            await page.wait_for_timeout(500)
        except Exception:
            pass
    
    async def _extract_main_content_smart(self, page, full_html: str) -> str:
        """
        智能提取主要内容
        
        策略：
        1. 使用选择器评分系统找到最佳内容区域
        2. 评估内容质量
        3. 如果选择器方法失败，使用 trafilatura
        """
        candidates = []
        
        for selector, base_score in self.PRIMARY_CONTENT_SELECTORS:
            try:
                elements = await page.query_selector_all(selector)
                for el in elements:
                    text = await el.inner_text()
                    text_length = len(text.strip())
                    
                    if text_length < 100:
                        continue
                    
                    score = self._calculate_content_score(el, text, base_score)
                    
                    html = await el.inner_html()
                    html = self._clean_html(html)
                    
                    candidates.append(ContentCandidate(
                        html=html,
                        text_length=text_length,
                        selector=selector,
                        score=score
                    ))
            except Exception:
                continue
        
        if candidates:
            candidates.sort(key=lambda x: x.score, reverse=True)
            best = candidates[0]
            
            if best.score > 50:
                return best.html
        
        trafilatura_content = self._extract_with_trafilatura(full_html)
        if trafilatura_content and len(trafilatura_content) > 100:
            return self._markdown_to_html(trafilatura_content)
        
        return self._clean_html(full_html)
    
    def _calculate_content_score(self, element, text: str, base_score: float) -> float:
        """
        计算内容区域的评分
        
        评分因素：
        - 基础选择器权重
        - 文本长度
        - 段落数量
        - 图片数量
        - 链接密度
        - 特殊关键词
        """
        score = float(base_score)
        
        text_length = len(text.strip())
        if text_length > 2000:
            score += 20
        elif text_length > 1000:
            score += 15
        elif text_length > 500:
            score += 10
        elif text_length > 200:
            score += 5
        
        paragraph_count = text.count('\n\n') + text.count('\n')
        if paragraph_count > 10:
            score += 10
        elif paragraph_count > 5:
            score += 5
        
        try:
            text_lower = text.lower()
            negative_keywords = ['评论', '相关文章', '推荐阅读', '热门', '广告', '赞助']
            for keyword in negative_keywords:
                if keyword in text_lower:
                    score -= 5
            
            positive_keywords = ['作者', '发布', '正文', '内容']
            for keyword in positive_keywords:
                if keyword in text_lower:
                    score += 3
        except Exception:
            pass
        
        return max(score, 0)
    
    def _extract_with_trafilatura(self, html: str) -> str:
        """使用 trafilatura 提取内容"""
        try:
            import trafilatura
            
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                favor_precision=True,
                favor_recall=False,
            )
            
            if content:
                return content.strip()
        except Exception:
            pass
        
        return ""
    
    def _markdown_to_html(self, markdown: str) -> str:
        """将 Markdown 转换回 HTML（用于统一处理）"""
        import html as html_module
        
        paragraphs = markdown.split('\n\n')
        html_parts = []
        
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            
            if p.startswith('# '):
                html_parts.append(f'<h1>{p[2:]}</h1>')
            elif p.startswith('## '):
                html_parts.append(f'<h2>{p[3:]}</h2>')
            elif p.startswith('### '):
                html_parts.append(f'<h3>{p[4:]}</h3>')
            elif p.startswith('```'):
                lang = ''
                code_content = p
                if '\n' in p:
                    first_line, rest = p.split('\n', 1)
                    lang = first_line[3:].strip()
                    code_content = rest.rstrip('`').strip()
                html_parts.append(f'<pre><code class="language-{lang}">{html_module.escape(code_content)}</code></pre>')
            elif p.startswith('!['):
                match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', p)
                if match:
                    alt, src = match.groups()
                    html_parts.append(f'<img src="{src}" alt="{alt}">')
            elif p.startswith('- ') or p.startswith('* '):
                items = []
                for line in p.split('\n'):
                    line = line.strip()
                    if line.startswith('- ') or line.startswith('* '):
                        items.append(f'<li>{line[2:]}</li>')
                html_parts.append(f'<ul>{"".join(items)}</ul>')
            else:
                html_parts.append(f'<p>{html_module.escape(p)}</p>')
        
        return '\n'.join(html_parts)
    
    def _clean_html(self, html: str) -> str:
        """清理 HTML 内容"""
        from bs4 import BeautifulSoup
        
        if not html:
            return ""
        
        soup = BeautifulSoup(html, "html.parser")
        
        for selector in self.REMOVE_SELECTORS:
            try:
                for tag in soup.select(selector):
                    tag.decompose()
            except Exception:
                continue
        
        for tag in soup.find_all(["nav", "header", "footer", "aside"]):
            tag.decompose()
        
        for tag in soup.find_all(class_=re.compile(r'\b(nav|header|footer|sidebar|menu|ad|advertisement|social|share|comment|related)\b', re.I)):
            tag.decompose()
        
        for tag in soup.find_all(id=re.compile(r'\b(nav|header|footer|sidebar|menu|ad|advertisement|social|share|comment|related)\b', re.I)):
            tag.decompose()
        
        for tag in soup.find_all(style=re.compile(r'display:\s*none|visibility:\s*hidden', re.I)):
            tag.decompose()
        
        for tag in soup.find_all(attrs={"aria-hidden": "true"}):
            if not tag.find_all(["img", "video", "audio"]):
                tag.decompose()
        
        for tag in soup.find_all("span"):
            if not tag.get_text(strip=True) and not tag.find_all("img"):
                tag.decompose()
        
        for tag in soup.find_all(["script", "style", "noscript", "iframe"]):
            tag.decompose()
        
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if href.startswith("javascript:") or href == "#":
                a.unwrap()
        
        return str(soup)
    
    def _clean_content(self, markdown: str) -> str:
        """清理 Markdown 内容"""
        if not markdown:
            return ""
        
        markdown = re.sub(r'<div[^>]*>', '\n', markdown)
        markdown = re.sub(r'</div>', '\n', markdown)
        markdown = re.sub(r'<section[^>]*>', '\n', markdown)
        markdown = re.sub(r'</section>', '\n', markdown)
        markdown = re.sub(r'<article[^>]*>', '\n', markdown)
        markdown = re.sub(r'</article>', '\n', markdown)
        markdown = re.sub(r'<span[^>]*>', '', markdown)
        markdown = re.sub(r'</span>', '', markdown)
        markdown = re.sub(r'<p[^>]*>', '\n', markdown)
        markdown = re.sub(r'</p>', '\n', markdown)
        markdown = re.sub(r'<br\s*/?>', '\n', markdown)
        markdown = re.sub(r'<[^>]+>', '', markdown)
        
        markdown = re.sub(r'\s*class="[^"]*"\s*', ' ', markdown)
        markdown = re.sub(r'\s*id="[^"]*"\s*', ' ', markdown)
        markdown = re.sub(r'\s*style="[^"]*"\s*', ' ', markdown)
        markdown = re.sub(r'div\s+', '', markdown)
        markdown = re.sub(r'/div', '', markdown)
        
        lines = markdown.split('\n')
        
        def is_skip_line(line: str) -> bool:
            stripped = line.strip()
            if not stripped:
                return False
            for pattern in self.SKIP_CONTENT_PATTERNS:
                if re.match(pattern, stripped):
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
            
            if stripped.startswith('div ') or stripped == '/div':
                continue
            
            if stripped.startswith('/'):
                continue
            
            if re.match(r'^\s*class="[^"]*"\s*$', stripped):
                continue
            if re.match(r'^\s*id="[^"]*"\s*$', stripped):
                continue
            
            cleaned_lines.append(line)
            if stripped:
                prev_line = stripped
        
        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n{4,}', '\n\n\n', result)
        
        result = self._remove_boilerplate(result)
        
        return result.strip()
    
    def _remove_boilerplate(self, content: str) -> str:
        """移除样板文字"""
        boilerplate_patterns = [
            r'扫码关注.*?\n',
            r'长按识别.*?二维码.*?\n',
            r'关注公众号.*?\n',
            r'分享到.*?\n',
            r'点赞.*?收藏.*?评论.*?\n',
            r'更多精彩内容.*?\n',
            r'相关推荐.*?\n',
            r'热门文章.*?\n',
            r'往期精选.*?\n',
            r'广告\s*\n',
            r'展开全文\s*\n',
            r'收起\s*\n',
            r'已编辑\s*\n',
            r'修改于.*?\n',
            r'\d+人赞同了该文章\s*\n',
            r'\d+人收藏\s*\n',
            r'\d+人点赞\s*\n',
            r'\d+人阅读\s*\n',
            r'阅读原文\s*\n',
            r'查看原文\s*\n',
            r'原文链接.*?\n',
            r'点击查看.*?\n',
            r'点击阅读.*?\n',
            r'赞赏\s*\n',
            r'打赏\s*\n',
            r'喜欢\s*\n',
            r'分享\s*\n',
            r'转发\s*\n',
        ]
        
        for pattern in boilerplate_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        return content


class GenericPlugin(BasePlugin):
    """通用平台插件"""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="generic",
            version="2.0.0",
            description="智能通用网站内容提取插件，支持多种网站结构",
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

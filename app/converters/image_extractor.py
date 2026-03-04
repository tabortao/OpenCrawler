"""
图片提取器模块

从 HTML 内容中提取图片 URL，支持多种懒加载格式
"""

import html
import re
from typing import Optional, List, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


class ImageExtractor:
    """
    图片提取器
    
    从 HTML 内容中提取图片 URL，支持多种懒加载格式
    """
    
    SMALL_IMAGE_PATTERNS = [
        "avatar", "thumbnail", "icon", "logo", "button",
        "badge", "flag", "emoji", "smiley", "emoticon",
        "!32x32", "!72x72", "!84x84", "!100x100",
        "/avatar/", "/icons/", "/logo/", "/thumb/",
        "/thumbnails/", "/favicon", "/sprite",
        "placeholder", "loading.gif", "spinner",
        "1x1", "blank.gif", "transparent",
        "data:image", "base64",
    ]
    
    IMAGE_DATA_ATTRIBUTES = [
        "data-original",
        "data-src",
        "data-lazy-src",
        "data-lazy",
        "data-url",
        "data-actualsrc",
        "data-srcset",
        "data-lazy-srcset",
        "data-image",
        "data-img",
        "data-cover",
        "data-background",
        "data-bg",
    ]
    
    @staticmethod
    def extract_from_html(html_content: str, base_url: str = "") -> list[str]:
        """
        从 HTML 内容中提取所有图片 URL
        
        Args:
            html_content: HTML 内容
            base_url: 基础 URL，用于解析相对路径
        
        Returns:
            图片 URL 列表
        """
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, "html.parser")
        image_urls = []
        
        for img in soup.find_all("img"):
            url = ImageExtractor._extract_image_url(img, base_url)
            if url and url not in image_urls:
                image_urls.append(url)
        
        for source in soup.find_all("source"):
            srcset = source.get("srcset", "")
            if srcset:
                urls = ImageExtractor._parse_srcset(srcset, base_url)
                for url in urls:
                    if url and url not in image_urls:
                        image_urls.append(url)
        
        for element in soup.find_all(attrs={"style": True}):
            style = element.get("style", "")
            bg_urls = ImageExtractor._extract_background_images(style, base_url)
            for url in bg_urls:
                if url and url not in image_urls:
                    image_urls.append(url)
        
        return image_urls
    
    @staticmethod
    def _extract_image_url(img, base_url: str = "") -> Optional[str]:
        """
        从 img 元素提取图片 URL
        
        Args:
            img: BeautifulSoup img 元素
            base_url: 基础 URL
        
        Returns:
            图片 URL 或 None
        """
        url_candidates = []
        
        for attr in ImageExtractor.IMAGE_DATA_ATTRIBUTES:
            url = img.get(attr, "")
            if url and not url.startswith("data:"):
                url_candidates.append(url)
        
        srcset = img.get("srcset", "")
        if srcset:
            urls = ImageExtractor._parse_srcset(srcset, base_url)
            url_candidates.extend(urls)
        
        src = img.get("src", "")
        if src and not src.startswith("data:"):
            url_candidates.append(src)
        
        for url in url_candidates:
            if not url or len(url) < 10:
                continue
            
            url_lower = url.lower()
            if any(pattern.lower() in url_lower for pattern in ImageExtractor.SMALL_IMAGE_PATTERNS):
                continue
            
            url = html.unescape(url)
            
            if url.startswith("//"):
                url = "https:" + url
            elif base_url and not url.startswith(("http://", "https://")):
                url = urljoin(base_url, url)
            
            if "toutiao" not in url.lower():
                if "?" in url:
                    url = url.split("?")[0]
            
            if ImageExtractor._is_valid_image_url(url):
                return url
        
        return None
    
    @staticmethod
    def _parse_srcset(srcset: str, base_url: str = "") -> List[str]:
        """
        解析 srcset 属性
        
        Args:
            srcset: srcset 属性值
            base_url: 基础 URL
        
        Returns:
            URL 列表
        """
        urls = []
        
        parts = srcset.split(",")
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            url_parts = part.split()
            if url_parts:
                url = url_parts[0]
                if url and not url.startswith("data:"):
                    if url.startswith("//"):
                        url = "https:" + url
                    elif base_url and not url.startswith(("http://", "https://")):
                        url = urljoin(base_url, url)
                    urls.append(url)
        
        return urls
    
    @staticmethod
    def _extract_background_images(style: str, base_url: str = "") -> List[str]:
        """
        从 CSS 样式中提取背景图片 URL
        
        Args:
            style: CSS 样式字符串
            base_url: 基础 URL
        
        Returns:
            URL 列表
        """
        urls = []
        
        patterns = [
            r'url\(["\']?([^"\')\s]+)["\']?\)',
            r'background-image:\s*url\(["\']?([^"\')\s]+)["\']?\)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, style, re.IGNORECASE)
            for url in matches:
                if url and not url.startswith("data:"):
                    if url.startswith("//"):
                        url = "https:" + url
                    elif base_url and not url.startswith(("http://", "https://")):
                        url = urljoin(base_url, url)
                    urls.append(url)
        
        return urls
    
    @staticmethod
    def extract_from_markdown(markdown: str) -> list[str]:
        """
        从 Markdown 内容中提取图片 URL
        
        Args:
            markdown: Markdown 内容
        
        Returns:
            图片 URL 列表
        """
        if not markdown:
            return []
        
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        matches = re.findall(pattern, markdown)
        
        image_urls = []
        for alt_text, url in matches:
            if url and not url.startswith("data:") and not url.startswith("images/"):
                if url not in image_urls:
                    image_urls.append(url)
        
        return image_urls
    
    @staticmethod
    def replace_urls_in_markdown(
        markdown: str,
        url_mapping: dict[str, str],
    ) -> str:
        """
        替换 Markdown 中的图片 URL
        
        Args:
            markdown: Markdown 内容
            url_mapping: URL 映射字典 {原URL: 新URL}
        
        Returns:
            替换后的 Markdown 内容
        """
        if not markdown or not url_mapping:
            return markdown
        
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        def replace_url(match):
            alt_text = match.group(1)
            url = match.group(2)
            
            if url in url_mapping:
                return f"![{alt_text}]({url_mapping[url]})"
            return match.group(0)
        
        return re.sub(pattern, replace_url, markdown)
    
    @staticmethod
    def filter_images_by_domain(
        image_urls: list[str],
        allowed_domains: list[str],
    ) -> list[str]:
        """
        按域名过滤图片 URL
        
        Args:
            image_urls: 图片 URL 列表
            allowed_domains: 允许的域名列表
        
        Returns:
            过滤后的图片 URL 列表
        """
        if not allowed_domains:
            return image_urls
        
        filtered = []
        for url in image_urls:
            try:
                domain = urlparse(url).netloc.lower()
                if any(allowed.lower() in domain for allowed in allowed_domains):
                    filtered.append(url)
            except Exception:
                continue
        
        return filtered
    
    @staticmethod
    def is_valid_image_url(url: str) -> bool:
        """
        检查是否为有效的图片 URL
        
        Args:
            url: 图片 URL
        
        Returns:
            是否有效
        """
        return ImageExtractor._is_valid_image_url(url)
    
    @staticmethod
    def _is_valid_image_url(url: str) -> bool:
        """
        内部方法：检查是否为有效的图片 URL
        
        Args:
            url: 图片 URL
        
        Returns:
            是否有效
        """
        if not url or url.startswith("data:"):
            return False
        
        if len(url) < 10:
            return False
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
        except Exception:
            return False
        
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".avif"]
        url_lower = url.lower()
        
        if any(ext in url_lower for ext in image_extensions):
            return True
        
        if url_lower.startswith("http://") or url_lower.startswith("https://"):
            return True
        
        return False
    
    @staticmethod
    def replace_urls_with_downloader(markdown: str, downloader) -> str:
        """
        使用下载器替换 Markdown 中的图片 URL
        
        Args:
            markdown: Markdown 内容
            downloader: 图片下载器实例
        
        Returns:
            替换后的 Markdown 内容
        """
        if not markdown:
            return markdown
        
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        def replace_image_url(match):
            alt_text = match.group(1)
            img_url = match.group(2)
            
            if not img_url or img_url.startswith("data:") or img_url.startswith("images/"):
                return match.group(0)
            
            clean_url = img_url.replace("&amp;", "&")
            local_path = downloader.download_image(clean_url)
            
            if local_path:
                return f"![{alt_text}]({local_path})"
            return match.group(0)
        
        return re.sub(pattern, replace_image_url, markdown)
    
    @staticmethod
    def get_image_dimensions(url: str) -> Optional[Tuple[int, int]]:
        """
        获取图片尺寸（需要下载图片）
        
        Args:
            url: 图片 URL
        
        Returns:
            (宽度, 高度) 元组或 None
        """
        try:
            import httpx
            from PIL import Image
            import io
            
            response = httpx.get(url, follow_redirects=True, timeout=10)
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
                return img.size
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def filter_small_images(
        image_urls: list[str],
        min_width: int = 100,
        min_height: int = 100,
    ) -> list[str]:
        """
        过滤小尺寸图片
        
        Args:
            image_urls: 图片 URL 列表
            min_width: 最小宽度
            min_height: 最小高度
        
        Returns:
            过滤后的图片 URL 列表
        """
        filtered = []
        
        for url in image_urls:
            dimensions = ImageExtractor.get_image_dimensions(url)
            if dimensions:
                width, height = dimensions
                if width >= min_width and height >= min_height:
                    filtered.append(url)
            else:
                filtered.append(url)
        
        return filtered

"""
图片提取器模块

从 HTML 内容中提取图片 URL
"""

import html
import re
from typing import Optional

from bs4 import BeautifulSoup


class ImageExtractor:
    """
    图片提取器
    
    从 HTML 内容中提取图片 URL
    """
    
    @staticmethod
    def extract_from_html(html_content: str) -> list[str]:
        """
        从 HTML 内容中提取所有图片 URL
        
        Args:
            html_content: HTML 内容
        
        Returns:
            图片 URL 列表
        """
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, "html.parser")
        image_urls = []
        
        for img in soup.find_all("img"):
            data_original = img.get("data-original", "")
            data_src = img.get("data-src", "")
            src = img.get("src", "")
            
            if data_original and not data_original.startswith("data:"):
                src = data_original
            elif data_src and not data_src.startswith("data:"):
                src = data_src
            
            if not src or src.startswith("data:"):
                continue
            
            if src == "..." or len(src) < 10:
                continue
            
            src = html.unescape(src)
            if src.startswith("//"):
                src = "https:" + src
            
            if "?" in src:
                src = src.split("?")[0]
            
            if src not in image_urls:
                image_urls.append(src)
        
        return image_urls
    
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
        
        from urllib.parse import urlparse
        
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
        if not url or url.startswith("data:"):
            return False
        
        if len(url) < 10:
            return False
        
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"]
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

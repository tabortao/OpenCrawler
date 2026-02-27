"""
图片下载器模块

提供图片下载和本地存储功能
"""

import hashlib
import os
from typing import Optional
from urllib.parse import urlparse

import httpx


class ImageDownloader:
    """
    图片下载器
    
    支持多平台图片下载，自动处理 Referer
    """
    
    PLATFORM_REFERERS = {
        "sspai": "https://sspai.com/",
        "wechat": "https://mp.weixin.qq.com/",
        "zhihu": "https://www.zhihu.com/",
        "xiaohongshu": "https://www.xiaohongshu.com/",
        "github": "https://github.com/",
    }
    
    PLATFORM_DOMAINS = {
        "sspai": ["sspai.com", "cdnfile.sspai.com", "cdn-static.sspai.com"],
        "wechat": ["mmbiz.qpic.cn", "wx.qlogo.cn", "mp.weixin.qq.com"],
        "zhihu": ["zhimg.com", "zhihu.com"],
        "xiaohongshu": ["xiaohongshu.com", "xhscdn.com", "sns-webpic-qc.xhscdn.com"],
        "github": ["github.com", "githubusercontent.com", "raw.githubusercontent.com", "camo.githubusercontent.com", "user-images.githubusercontent.com"],
    }
    
    def __init__(self, output_dir: str):
        """
        初始化图片下载器
        
        Args:
            output_dir: 输出目录
        """
        self.images_dir = os.path.join(output_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        
        self.client = httpx.Client(
            timeout=30,
            follow_redirects=True,
            headers=self._get_default_headers(),
        )
        self.downloaded: dict[str, str] = {}
    
    def _get_default_headers(self) -> dict:
        """获取默认请求头"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
    
    def _detect_platform_from_url(self, url: str) -> Optional[str]:
        """
        根据 URL 检测平台
        
        Args:
            url: 图片 URL
        
        Returns:
            平台名称
        """
        url_lower = url.lower()
        
        for platform, domains in self.PLATFORM_DOMAINS.items():
            if any(domain in url_lower for domain in domains):
                return platform
        
        return None
    
    def _get_referer_for_url(self, url: str) -> str:
        """
        获取图片 URL 对应的 Referer
        
        Args:
            url: 图片 URL
        
        Returns:
            Referer 字符串
        """
        platform = self._detect_platform_from_url(url)
        if platform and platform in self.PLATFORM_REFERERS:
            return self.PLATFORM_REFERERS[platform]
        return ""
    
    def _get_image_extension(self, url: str, content_type: str = "", content: bytes = b"") -> str:
        """
        获取图片扩展名
        
        Args:
            url: 图片 URL
            content_type: 内容类型
            content: 响应内容（用于检测实际格式）
        
        Returns:
            图片扩展名
        """
        if content_type:
            content_type_lower = content_type.lower()
            if "svg" in content_type_lower or "svg+xml" in content_type_lower:
                return ".svg"
            elif "webp" in content_type_lower:
                return ".webp"
            elif "png" in content_type_lower:
                return ".png"
            elif "gif" in content_type_lower:
                return ".gif"
            elif "jpeg" in content_type_lower or "jpg" in content_type_lower:
                return ".jpg"
        
        if content:
            content_start = content[:100].lower()
            if b'<svg' in content_start or b'<?xml' in content_start:
                return ".svg"
            elif content[:8] == b'\x89PNG\r\n\x1a\n':
                return ".png"
            elif content[:6] in (b'GIF87a', b'GIF89a'):
                return ".gif"
            elif content[:2] == b'\xff\xd8':
                return ".jpg"
            elif content[:4] == b'RIFF' and content[8:12] == b'WEBP':
                return ".webp"
        
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in [".svg", ".webp", ".png", ".gif", ".jpg", ".jpeg"]:
            if path.endswith(ext):
                return ext
        
        return ".jpg"
    
    def _clean_url(self, url: str) -> str:
        """
        清理 URL 中的 HTML 实体
        
        Args:
            url: 原始 URL
        
        Returns:
            清理后的 URL
        """
        url = url.replace("&amp;", "&")
        url = url.replace("&lt;", "<")
        url = url.replace("&gt;", ">")
        url = url.replace("&quot;", '"')
        
        if url.startswith("//"):
            url = "https:" + url
        
        return url
    
    def download_image(self, url: str) -> Optional[str]:
        """
        下载图片到本地
        
        Args:
            url: 图片 URL
        
        Returns:
            本地相对路径，失败返回 None
        """
        if url in self.downloaded:
            return self.downloaded[url]
        
        try:
            clean_url = self._clean_url(url)
            
            headers = self._get_default_headers()
            referer = self._get_referer_for_url(clean_url)
            if referer:
                headers["Referer"] = referer
            
            response = self.client.get(clean_url, headers=headers)
            if response.status_code != 200:
                return None
            
            content_type = response.headers.get("content-type", "")
            content = response.content
            ext = self._get_image_extension(url, content_type, content)
            
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            safe_hash = ''.join(c for c in url_hash if c.isalnum())
            filename = f"{safe_hash}{ext}"
            filepath = os.path.join(self.images_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(content)
            
            relative_path = f"images/{filename}"
            self.downloaded[url] = relative_path
            return relative_path
        
        except Exception as e:
            print(f"Failed to download image: {url[:50]}... Error: {e}")
            return None
    
    def download_images(self, urls: list[str]) -> dict[str, Optional[str]]:
        """
        批量下载图片
        
        Args:
            urls: 图片 URL 列表
        
        Returns:
            URL 到本地路径的映射
        """
        results = {}
        for url in urls:
            results[url] = self.download_image(url)
        return results
    
    def close(self):
        """关闭 HTTP 客户端"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

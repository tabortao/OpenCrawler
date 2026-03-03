"""
图片下载器模块

提供图片下载和本地存储功能
"""

import hashlib
import os
import time
from datetime import datetime
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
        "toutiao": "https://www.toutiao.com/",
    }
    
    PLATFORM_DOMAINS = {
        "sspai": ["sspai.com", "cdnfile.sspai.com", "cdn-static.sspai.com"],
        "wechat": ["mmbiz.qpic.cn", "wx.qlogo.cn", "mp.weixin.qq.com"],
        "zhihu": ["zhimg.com", "zhihu.com"],
        "xiaohongshu": ["xiaohongshu.com", "xhscdn.com", "sns-webpic-qc.xhscdn.com"],
        "github": ["github.com", "githubusercontent.com", "raw.githubusercontent.com", "camo.githubusercontent.com", "user-images.githubusercontent.com"],
        "toutiao": ["toutiao.com", "p3-sign.toutiaoimg.com", "p6-sign.toutiaoimg.com", "p9-sign.toutiaoimg.com"],
    }
    
    def __init__(self, output_dir: str, compress: bool = False, compress_quality: int = 85):
        """
        初始化图片下载器
        
        Args:
            output_dir: 输出目录
            compress: 是否压缩图片
            compress_quality: 压缩质量 (1-95)
        """
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        
        self.compress = compress
        self.compress_quality = compress_quality
        
        self.client = httpx.Client(
            timeout=30,
            follow_redirects=True,
            headers=self._get_default_headers(),
        )
        self.downloaded: dict[str, str] = {}
        
        # 图片计数器，用于生成唯一文件名
        self._image_counter = 0
        
        # 压缩统计
        self._compress_stats = {"total_original": 0, "total_compressed": 0, "count": 0}
        
        # 用于今日头条图片的浏览器实例
        self._playwright = None
        self._browser = None
        self._context = None
    
    def _get_default_headers(self) -> dict:
        """获取默认请求头"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
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
    
    def _compress_image(self, filepath: str) -> bool:
        """
        压缩图片
        
        Args:
            filepath: 图片文件路径
        
        Returns:
            是否成功
        """
        from app.utils.image_compressor import ImageCompressor
        
        try:
            compressor = ImageCompressor(quality=self.compress_quality)
            success, original_size, compressed_size = compressor.compress_in_place(filepath)
            
            if success:
                self._compress_stats["total_original"] += original_size
                self._compress_stats["total_compressed"] += compressed_size
                self._compress_stats["count"] += 1
            
            return success
        except Exception as e:
            print(f"压缩图片失败: {filepath} - {e}")
            return False
    
    def get_compress_stats(self) -> dict:
        """
        获取压缩统计信息
        
        Returns:
            压缩统计字典
        """
        stats = self._compress_stats.copy()
        if stats["total_original"] > 0:
            stats["saved_bytes"] = stats["total_original"] - stats["total_compressed"]
            stats["saved_percent"] = (stats["saved_bytes"] / stats["total_original"]) * 100
        else:
            stats["saved_bytes"] = 0
            stats["saved_percent"] = 0
        return stats
    
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
    
    async def _download_with_playwright(self, url: str) -> Optional[bytes]:
        """
        使用 Playwright 下载图片
        
        Args:
            url: 图片 URL
        
        Returns:
            图片内容，失败返回 None
        """
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        
        try:
            if not self._playwright:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--remote-debugging-port=9222",
                    ],
                )
                self._context = await self._browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                    timezone_id="Asia/Shanghai",
                )
            
            page = await self._context.new_page()
            
            # 导航到图片 URL
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # 直接获取页面内容
            content = await page.content()
            
            # 检查是否为图片
            if "<html" in content:
                # 如果返回的是 HTML，可能是 403 页面
                print(f"Playwright got HTML instead of image for {url[:50]}...")
                return None
            
            # 获取图片内容
            response = await page.request.get(url)
            if response.status == 200:
                content = await response.body()
                return content
            else:
                print(f"Playwright HTTP {response.status} for {url[:50]}...")
                return None
            
            return None
        
        except PlaywrightTimeoutError:
            print(f"Playwright timeout for {url[:50]}...")
            return None
        except Exception as e:
            print(f"Playwright error for {url[:50]}... Error: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            if 'page' in locals():
                await page.close()
    
    async def _download_image_async(self, url: str) -> Optional[str]:
        """
        异步下载图片
        
        Args:
            url: 图片 URL
        
        Returns:
            本地相对路径，失败返回 None
        """
        
        if url in self.downloaded:
            return self.downloaded[url]
        
        try:
            clean_url = self._clean_url(url)
            
            # 检测是否为今日头条图片
            if "toutiao" in clean_url.lower():
                # 使用 Playwright 下载今日头条图片
                print(f"使用 Playwright 下载今日头条图片: {clean_url[:50]}...")
                content = await self._download_with_playwright(clean_url)
            else:
                # 使用 httpx 下载其他图片
                headers = self._get_default_headers()
                referer = self._get_referer_for_url(clean_url)
                if referer:
                    headers["Referer"] = referer
                
                response = self.client.get(clean_url, headers=headers, timeout=30, follow_redirects=True)
                
                if response.status_code != 200:
                    print(f"HTTP {response.status_code} for {clean_url[:50]}...")
                    return None
                
                content = response.content
            
            # 检查响应内容
            if not content or len(content) < 100:
                print(f"Empty or small content for {clean_url[:50]}...")
                return None
            
            # 获取图片扩展名
            ext = self._get_image_extension(url, content_type="", content=content)
            
            # 生成文件名：日期+时间+自增计数器（更易读）
            now = datetime.now()
            date_time_str = now.strftime("%Y%m%d_%H%M%S")
            self._image_counter += 1
            filename = f"{date_time_str}_{self._image_counter:03d}{ext}"
            
            # 创建年月子目录
            year = now.strftime("%Y")
            month = now.strftime("%m")
            sub_dir = os.path.join(self.images_dir, year, month)
            os.makedirs(sub_dir, exist_ok=True)
            
            filepath = os.path.join(sub_dir, filename)
            
            # 保存图片
            with open(filepath, "wb") as f:
                f.write(content)
            
            # 压缩图片
            if self.compress:
                self._compress_image(filepath)
            
            # 相对路径：images/年/月/文件名
            relative_path = f"images/{year}/{month}/{filename}"
            self.downloaded[url] = relative_path
            print(f"Downloaded: {relative_path}")
            return relative_path
        
        except Exception as e:
            print(f"Failed to download image: {url[:50]}... Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def download_image(self, url: str) -> Optional[str]:
        """
        下载图片到本地
        
        Args:
            url: 图片 URL
        
        Returns:
            本地相对路径，失败返回 None
        """
        import asyncio
        import concurrent.futures
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop is not None:
            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(self._download_image_async(url))
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_loop)
                return future.result()
        else:
            return asyncio.run(self._download_image_async(url))
    
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
        """关闭 HTTP 客户端和浏览器"""
        # 关闭 HTTP 客户端
        self.client.close()
        
        # 关闭 Playwright
        import asyncio
        import concurrent.futures
        
        async def close_playwright():
            try:
                if self._context:
                    await self._context.close()
                    self._context = None
            except Exception:
                pass
            
            try:
                if self._browser:
                    await self._browser.close()
                    self._browser = None
            except Exception:
                pass
            
            try:
                if self._playwright:
                    await self._playwright.stop()
                    self._playwright = None
            except Exception:
                pass
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop is not None:
            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(close_playwright())
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_loop)
                future.result()
        else:
            asyncio.run(close_playwright())
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

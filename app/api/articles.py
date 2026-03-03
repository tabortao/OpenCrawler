"""
文章 API 模块

提供文章保存相关的 API 接口
"""

import asyncio
import os
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.exceptions import CrawlerException, URLValidationError, TimeoutError
from app.crawlers.factory import CrawlerFactory
from app.crawlers.image_downloader import ImageDownloader
from app.utils.url import is_valid_url, detect_platform
from app.utils.file import sanitize_filename, get_unique_filepath
from app.converters.markdown import MarkdownConverter
from app.converters.image_extractor import ImageExtractor

router = APIRouter()


class ArticleCreateRequest(BaseModel):
    """文章创建请求模型"""
    url: str = Field(..., description="要提取并保存的网页 URL")
    download_images: bool = Field(default=False, description="是否下载图片到本地")
    compress_images: bool = Field(default=False, description="是否压缩下载的图片")
    compress_quality: int = Field(default=85, ge=1, le=95, description="图片压缩质量 (1-95)")


class ArticleCreateResponse(BaseModel):
    """文章创建响应模型"""
    title: str = Field(..., description="文章标题")
    url: str = Field(..., description="原始 URL")
    filepath: str = Field(..., description="保存的文件路径")
    compress_stats: dict = Field(default_factory=dict, description="图片压缩统计信息")


@router.post("/articles", response_model=ArticleCreateResponse)
async def create_article(request: ArticleCreateRequest):
    """
    创建文章
    
    从指定 URL 提取内容并保存为 Markdown 文件
    """
    if not is_valid_url(request.url):
        raise URLValidationError(
            message="URL 格式不正确，请提供有效的 HTTP/HTTPS URL",
            url=request.url,
        )
    
    try:
        result = await asyncio.wait_for(
            CrawlerFactory.crawl(request.url),
            timeout=300.0,
        )
        
        platform = detect_platform(request.url)
        filepath, compress_stats = save_article(
            title=result.title,
            url=result.url,
            markdown=result.markdown,
            html=result.html,
            image_urls=result.image_urls,
            download_images=request.download_images,
            compress_images=request.compress_images,
            compress_quality=request.compress_quality,
            platform=platform,
        )
        
        return {
            "title": result.title,
            "url": result.url,
            "filepath": filepath,
            "compress_stats": compress_stats,
        }
    
    except asyncio.TimeoutError:
        raise TimeoutError(
            message="抓取超时，请稍后重试或检查目标网站是否可访问",
            url=request.url,
            timeout_seconds=300,
        )
    except CrawlerException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "Cookie" in error_msg:
            raise CrawlerException(
                message=error_msg,
                error_code="AUTHENTICATION_REQUIRED",
                status_code=401,
            )
        raise CrawlerException(
            message=f"保存失败: {error_msg}",
            error_code="INTERNAL_ERROR",
            status_code=500,
        )


def save_article(
    title: str,
    url: str,
    markdown: str,
    html: str = "",
    image_urls: list[str] = None,
    download_images: bool = False,
    compress_images: bool = False,
    compress_quality: int = 85,
    platform: str = "generic",
) -> tuple[str, dict]:
    """
    保存文章为 Markdown 文件
    
    Args:
        title: 文章标题
        url: 原始 URL
        markdown: Markdown 内容
        html: HTML 内容
        image_urls: 图片 URL 列表
        download_images: 是否下载图片
        compress_images: 是否压缩图片
        compress_quality: 压缩质量
        platform: 平台名称
    
    Returns:
        (保存的文件路径, 压缩统计信息)
    """
    output_dir = settings.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    safe_title = sanitize_filename(title) or "untitled"
    filename = f"{today}_{safe_title}.md"
    filepath = get_unique_filepath(output_dir, filename)
    
    print(f"保存文章: {title}")
    print(f"下载图片: {download_images}")
    print(f"压缩图片: {compress_images}")
    print(f"压缩质量: {compress_quality}")
    print(f"HTML 长度: {len(html) if html else 0}")
    print(f"图片 URL 数量: {len(image_urls) if image_urls else 0}")
    print(f"平台: {platform}")
    
    compress_stats = {}
    
    if download_images:
        article_dir = os.path.dirname(filepath)
        
        if html:
            print("使用 html_to_markdown_with_images")
            markdown, compress_stats = html_to_markdown_with_images(
                html, image_urls or [], article_dir, platform, compress_images, compress_quality
            )
        elif image_urls:
            print("使用 download_images_in_markdown")
            markdown, compress_stats = download_images_in_markdown(
                markdown, image_urls, article_dir, compress_images, compress_quality
            )
        else:
            print("没有 HTML 和图片 URL，跳过下载")
    else:
        print("未启用图片下载")
    
    formatted_markdown = format_markdown_content(markdown)
    
    publish_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    full_document = MarkdownConverter.generate_document(
        title=title,
        author="",
        publish_time=publish_time,
        content=formatted_markdown,
        source_url=url,
    )
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_document)
    
    print(f"文章保存到: {filepath}")
    return filepath, compress_stats


def html_to_markdown_with_images(
    html: str,
    image_urls: list[str],
    output_dir: str,
    platform: str = "generic",
    compress: bool = False,
    compress_quality: int = 85,
) -> tuple[str, dict]:
    """
    将 HTML 转换为 Markdown 并下载图片
    
    Args:
        html: HTML 内容
        image_urls: 图片 URL 列表
        output_dir: 输出目录
        platform: 平台名称
        compress: 是否压缩图片
        compress_quality: 压缩质量
    
    Returns:
        (Markdown 内容, 压缩统计信息)
    """
    if not html:
        return "", {}
    
    # 先转换为 Markdown
    markdown = MarkdownConverter.convert_html_to_markdown(html, platform=platform)
    
    # 对于今日头条，直接返回原始 Markdown，保留原始图片 URL
    if platform == "toutiao":
        print("对于今日头条，保留原始图片 URL")
        return markdown, {}
    
    # 对于其他平台，尝试下载图片
    with ImageDownloader(output_dir, compress=compress, compress_quality=compress_quality) as downloader:
        print("使用 ImageExtractor.replace_urls_with_downloader 下载图片")
        markdown = ImageExtractor.replace_urls_with_downloader(markdown, downloader)
        compress_stats = downloader.get_compress_stats() if compress else {}
    
    return markdown, compress_stats


def download_images_in_markdown(
    markdown: str,
    image_urls: list[str],
    output_dir: str,
    compress: bool = False,
    compress_quality: int = 85,
) -> tuple[str, dict]:
    """
    下载 Markdown 中的图片
    
    Args:
        markdown: Markdown 内容
        image_urls: 图片 URL 列表
        output_dir: 输出目录
        compress: 是否压缩图片
        compress_quality: 压缩质量
    
    Returns:
        (Markdown 内容, 压缩统计信息)
    """
    if not markdown:
        return markdown, {}
    
    with ImageDownloader(output_dir, compress=compress, compress_quality=compress_quality) as downloader:
        markdown = ImageExtractor.replace_urls_with_downloader(markdown, downloader)
        compress_stats = downloader.get_compress_stats() if compress else {}
    
    return markdown, compress_stats


def format_markdown_content(markdown: str) -> str:
    """格式化 Markdown 内容"""
    if not markdown:
        return ""
    
    lines = markdown.split('\n')
    formatted_lines = []
    in_code_block = False
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith('```'):
            if in_code_block:
                formatted_lines.append('```')
                in_code_block = False
            else:
                in_code_block = True
                lang = stripped[3:].strip() or "text"
                formatted_lines.append(f"```{lang}")
        else:
            formatted_lines.append(line)
    
    result = '\n'.join(formatted_lines)
    result = result.replace('\n\n\n\n', '\n\n\n')
    
    return result.strip()

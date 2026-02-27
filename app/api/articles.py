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


class ArticleCreateResponse(BaseModel):
    """文章创建响应模型"""
    title: str = Field(..., description="文章标题")
    url: str = Field(..., description="原始 URL")
    filepath: str = Field(..., description="保存的文件路径")


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
        filepath = save_article(
            title=result.title,
            url=result.url,
            markdown=result.markdown,
            html=result.html,
            image_urls=result.image_urls,
            download_images=request.download_images,
            platform=platform,
        )
        
        return {
            "title": result.title,
            "url": result.url,
            "filepath": filepath,
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
    platform: str = "generic",
) -> str:
    """
    保存文章为 Markdown 文件
    
    Args:
        title: 文章标题
        url: 原始 URL
        markdown: Markdown 内容
        html: HTML 内容
        image_urls: 图片 URL 列表
        download_images: 是否下载图片
        platform: 平台名称
    
    Returns:
        保存的文件路径
    """
    output_dir = settings.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    safe_title = sanitize_filename(title) or "untitled"
    filename = f"{today}_{safe_title}.md"
    filepath = get_unique_filepath(output_dir, filename)
    
    if download_images:
        article_dir = os.path.dirname(filepath)
        
        if html:
            markdown = html_to_markdown_with_images(html, image_urls or [], article_dir, platform)
        elif image_urls:
            markdown = download_images_in_markdown(markdown, image_urls, article_dir)
    
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
    
    return filepath


def html_to_markdown_with_images(
    html: str,
    image_urls: list[str],
    output_dir: str,
    platform: str = "generic",
) -> str:
    """将 HTML 转换为 Markdown 并下载图片"""
    if not html:
        return ""
    
    with ImageDownloader(output_dir) as downloader:
        markdown = MarkdownConverter.convert_html_to_markdown(html, platform=platform)
        markdown = ImageExtractor.replace_urls_with_downloader(markdown, downloader)
        return markdown


def download_images_in_markdown(
    markdown: str,
    image_urls: list[str],
    output_dir: str,
) -> str:
    """下载 Markdown 中的图片"""
    if not markdown:
        return markdown
    
    with ImageDownloader(output_dir) as downloader:
        return ImageExtractor.replace_urls_with_downloader(markdown, downloader)


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

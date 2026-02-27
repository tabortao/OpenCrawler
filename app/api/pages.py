"""
页面 API 模块

提供页面内容提取相关的 API 接口
"""

import asyncio

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.exceptions import CrawlerException, URLValidationError, TimeoutError
from app.plugins.registry import plugin_registry
from app.crawlers.factory import CrawlerFactory
from app.utils.url import is_valid_url, detect_platform

router = APIRouter()


class PageExtractRequest(BaseModel):
    """页面提取请求模型"""
    url: str = Field(..., description="要提取内容的网页 URL")


class PageExtractResponse(BaseModel):
    """页面提取响应模型"""
    title: str = Field(..., description="页面标题")
    url: str = Field(..., description="原始 URL")
    markdown: str = Field(..., description="Markdown 内容")
    html: str = Field(default="", description="HTML 内容")
    image_urls: list[str] = Field(default_factory=list, description="图片 URL 列表")


class PageTitleResponse(BaseModel):
    """页面标题响应模型"""
    url: str = Field(..., description="请求的 URL")
    title: str = Field(..., description="页面标题")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误详情")


@router.get("/pages/title", response_model=PageTitleResponse)
async def get_page_title(url: str = Query(..., description="要获取标题的网页 URL")):
    """
    获取网页标题
    
    根据提供的 URL 获取网页标题，如果网页没有标题则返回提示信息
    """
    if not is_valid_url(url):
        raise URLValidationError(
            message="URL 格式不正确，请提供有效的 HTTP/HTTPS URL",
            url=url,
        )
    
    try:
        result = await asyncio.wait_for(
            CrawlerFactory.crawl(url),
            timeout=300.0,
        )
        
        title = result.title
        
        if not title or title.strip() == "":
            raise CrawlerException(
                message="该网页没有标题",
                error_code="TITLE_NOT_FOUND",
                status_code=404,
            )
        
        return {
            "url": url,
            "title": title,
        }
    
    except asyncio.TimeoutError:
        raise TimeoutError(
            message="请求超时，请稍后重试或检查目标网站是否可访问",
            url=url,
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
            message=f"获取标题失败: {error_msg}",
            error_code="INTERNAL_ERROR",
            status_code=500,
        )


@router.post("/pages/extract", response_model=PageExtractResponse)
async def extract_page(request: PageExtractRequest):
    """
    提取页面内容
    
    从指定 URL 提取网页内容并转换为 Markdown 格式
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
        
        return {
            "title": result.title,
            "url": result.url,
            "markdown": result.markdown,
            "html": result.html,
            "image_urls": result.image_urls,
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
            message=f"抓取失败: {error_msg}",
            error_code="INTERNAL_ERROR",
            status_code=500,
        )

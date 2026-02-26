"""
多平台网页 Markdown 提取 API

基于 FastAPI + Playwright 的网页内容提取服务
支持 GitHub、知乎、小红书、微信公众号等平台
"""

import asyncio
import os
import sys

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from crawler import extract_url, save_article
from utils import detect_platform, is_valid_url

print(f"[Main] Loaded crawler module, checking extract_url...")
import crawler
print(f"[Main] crawler.crawl method exists: {hasattr(crawler, 'WebCrawler')}")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv()

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(
    title="多平台网页 Markdown 提取 API",
    description="基于 FastAPI + Playwright 的网页内容提取服务，支持 GitHub、知乎、小红书、微信公众号等平台",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ==================== 响应模型 ====================

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


class ArticleCreateRequest(BaseModel):
    """文章创建请求模型"""
    url: str = Field(..., description="要提取并保存的网页 URL")
    download_images: bool = Field(default=False, description="是否下载图片到本地")


class ArticleCreateResponse(BaseModel):
    """文章创建响应模型"""
    title: str = Field(..., description="文章标题")
    url: str = Field(..., description="原始 URL")
    filepath: str = Field(..., description="保存的文件路径")


class PageTitleResponse(BaseModel):
    """页面标题响应模型"""
    url: str = Field(..., description="请求的 URL")
    title: str = Field(..., description="页面标题")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误详情")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")
    version: str = Field(..., description="API 版本")


# ==================== 异常处理 ====================

class APIException(Exception):
    """API 异常基类"""
    def __init__(self, status_code: int, error: str, message: str):
        self.status_code = status_code
        self.error = error
        self.message = message


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """处理 API 异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error, "message": exc.message},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理 HTTP 异常"""
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP_ERROR", "message": str(exc.detail)},
    )


# ==================== RESTful API v1 ====================

@app.get("/api/v1/health", response_model=HealthResponse, tags=["系统"])
async def health_check():
    """
    健康检查
    
    检查服务是否正常运行
    """
    return {
        "status": "healthy",
        "service": "Web Markdown Extractor",
        "version": "2.0.0",
    }


@app.get("/api/v1/pages/title", response_model=PageTitleResponse, tags=["页面"])
async def get_page_title(url: str = Query(..., description="要获取标题的网页 URL")):
    """
    获取网页标题
    
    根据提供的 URL 获取网页标题，如果网页没有标题则返回提示信息
    """
    # 验证 URL 格式
    if not is_valid_url(url):
        raise APIException(
            status_code=400,
            error="INVALID_URL",
            message="URL 格式不正确，请提供有效的 HTTP/HTTPS URL",
        )
    
    try:
        result = await asyncio.wait_for(
            extract_url(url),
            timeout=300.0,
        )
        
        title = result.get("title", "")
        
        # 如果标题为空，返回提示信息
        if not title or title.strip() == "":
            raise APIException(
                status_code=404,
                error="TITLE_NOT_FOUND",
                message="该网页没有标题",
            )
        
        return {
            "url": url,
            "title": title,
        }
        
    except APIException:
        raise
    except asyncio.TimeoutError:
        raise APIException(
            status_code=504,
            error="TIMEOUT",
            message="请求超时，请稍后重试或检查目标网站是否可访问",
        )
    except ValueError as e:
        raise APIException(
            status_code=422,
            error="CONTENT_ERROR",
            message=str(e) or "页面内容为空或无法解析",
        )
    except Exception as e:
        error_msg = str(e)
        if "Cookie" in error_msg:
            raise APIException(
                status_code=401,
                error="AUTHENTICATION_REQUIRED",
                message=error_msg,
            )
        raise APIException(
            status_code=500,
            error="INTERNAL_ERROR",
            message=f"获取标题失败: {error_msg}",
        )


@app.post("/api/v1/pages/extract", response_model=PageExtractResponse, tags=["页面"])
async def extract_page(request: PageExtractRequest):
    """
    提取页面内容
    
    从指定 URL 提取网页内容并转换为 Markdown 格式
    """
    # 验证 URL 格式
    if not is_valid_url(request.url):
        raise APIException(
            status_code=400,
            error="INVALID_URL",
            message="URL 格式不正确，请提供有效的 HTTP/HTTPS URL",
        )
    
    try:
        result = await asyncio.wait_for(
            extract_url(request.url),
            timeout=300.0,
        )
        
        return {
            "title": result.get("title", ""),
            "url": result.get("url", request.url),
            "markdown": result.get("markdown", ""),
            "html": result.get("html", ""),
            "image_urls": result.get("image_urls", []),
        }
        
    except asyncio.TimeoutError:
        raise APIException(
            status_code=504,
            error="TIMEOUT",
            message="抓取超时，请稍后重试或检查目标网站是否可访问",
        )
    except ValueError as e:
        raise APIException(
            status_code=422,
            error="CONTENT_ERROR",
            message=str(e) or "页面内容为空或无法解析",
        )
    except Exception as e:
        error_msg = str(e)
        if "Cookie" in error_msg:
            raise APIException(
                status_code=401,
                error="AUTHENTICATION_REQUIRED",
                message=error_msg,
            )
        raise APIException(
            status_code=500,
            error="INTERNAL_ERROR",
            message=f"抓取失败: {error_msg}",
        )


@app.post("/api/v1/articles", response_model=ArticleCreateResponse, tags=["文章"])
async def create_article(request: ArticleCreateRequest):
    """
    创建文章
    
    从指定 URL 提取内容并保存为 Markdown 文件
    """
    # 验证 URL 格式
    if not is_valid_url(request.url):
        raise APIException(
            status_code=400,
            error="INVALID_URL",
            message="URL 格式不正确，请提供有效的 HTTP/HTTPS URL",
        )
    
    try:
        result = await asyncio.wait_for(
            extract_url(request.url),
            timeout=300.0,
        )
        
        platform = detect_platform(request.url)
        filepath = save_article(
            title=result["title"],
            url=result["url"],
            markdown=result["markdown"],
            html=result.get("html", ""),
            image_urls=result.get("image_urls", []),
            download_images=request.download_images,
            platform=platform,
        )
        
        return {
            "title": result["title"],
            "url": result["url"],
            "filepath": filepath,
        }
        
    except asyncio.TimeoutError:
        raise APIException(
            status_code=504,
            error="TIMEOUT",
            message="抓取超时，请稍后重试或检查目标网站是否可访问",
        )
    except ValueError as e:
        raise APIException(
            status_code=422,
            error="CONTENT_ERROR",
            message=str(e) or "页面内容为空或无法解析",
        )
    except Exception as e:
        error_msg = str(e)
        if "Cookie" in error_msg:
            raise APIException(
                status_code=401,
                error="AUTHENTICATION_REQUIRED",
                message=error_msg,
            )
        raise APIException(
            status_code=500,
            error="INTERNAL_ERROR",
            message=f"保存失败: {error_msg}",
        )


# ==================== 兼容旧 API（已废弃） ====================

@app.get("/extract", deprecated=True, tags=["已废弃"])
async def extract_content_legacy(url: str = Query(..., description="要提取内容的网页 URL")):
    """
    [已废弃] 请使用 POST /api/v1/pages/extract
    """
    return await extract_page(PageExtractRequest(url=url))


@app.get("/save", deprecated=True, tags=["已废弃"])
async def save_content_legacy(
    url: str = Query(..., description="要提取并保存的网页 URL"),
    download_images: bool = Query(False, description="是否下载图片到本地"),
):
    """
    [已废弃] 请使用 POST /api/v1/articles
    """
    return await create_article(ArticleCreateRequest(url=url, download_images=download_images))


@app.get("/health", deprecated=True, tags=["已废弃"])
async def health_check_legacy():
    """
    [已废弃] 请使用 GET /api/v1/health
    """
    return await health_check()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
    )

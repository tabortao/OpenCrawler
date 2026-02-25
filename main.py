import asyncio
import os
import sys

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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
    description="基于 FastAPI + Crawlee + Playwright 的网页内容提取服务，支持 GitHub、知乎、小红书、微信公众号等平台",
    version="1.0.0",
)


class ExtractResponse(BaseModel):
    status: str
    title: str
    url: str
    markdown: str


class SaveResponse(BaseModel):
    status: str
    title: str
    url: str
    filepath: str


class ErrorResponse(BaseModel):
    status: str
    error: str
    detail: str


@app.get("/extract", response_model=ExtractResponse, responses={
    400: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
})
async def extract_content(url: str = Query(..., description="要提取内容的网页 URL")):
    if not is_valid_url(url):
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "error": "INVALID_URL",
                "detail": "URL 格式不正确，请提供有效的 HTTP/HTTPS URL",
            },
        )

    try:
        result = await asyncio.wait_for(
            extract_url(url),
            timeout=300.0,
        )
        return JSONResponse(content=result)

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": "TIMEOUT",
                "detail": "抓取超时，请稍后重试或检查目标网站是否可访问",
            },
        )

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "status": "error",
                "error": "EMPTY_CONTENT",
                "detail": str(e) or "页面内容为空或无法解析",
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": "CRAWL_ERROR",
                "detail": f"抓取失败: {str(e)}",
            },
        )


@app.get("/save", response_model=SaveResponse, responses={
    400: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
})
async def save_content(
    url: str = Query(..., description="要提取并保存的网页 URL"),
    download_images: bool = Query(False, description="是否下载图片到本地"),
):
    if not is_valid_url(url):
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "error": "INVALID_URL",
                "detail": "URL 格式不正确，请提供有效的 HTTP/HTTPS URL",
            },
        )

    try:
        result = await asyncio.wait_for(
            extract_url(url),
            timeout=300.0,
        )

        platform = detect_platform(url)
        filepath = save_article(
            title=result["title"],
            url=result["url"],
            markdown=result["markdown"],
            html=result.get("html", ""),
            image_urls=result.get("image_urls", []),
            download_images=download_images,
            platform=platform,
        )

        return JSONResponse(content={
            "status": "success",
            "title": result["title"],
            "url": result["url"],
            "filepath": filepath,
        })

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": "TIMEOUT",
                "detail": "抓取超时，请稍后重试或检查目标网站是否可访问",
            },
        )

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "status": "error",
                "error": "EMPTY_CONTENT",
                "detail": str(e) or "页面内容为空或无法解析",
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": "SAVE_ERROR",
                "detail": f"保存失败: {str(e)}",
            },
        )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Web Markdown Extractor"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
    )

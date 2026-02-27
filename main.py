"""
OpenCrawler - 多平台网页 Markdown 提取 API

基于 FastAPI + Playwright 的网页内容提取服务
支持 GitHub、知乎、小红书、微信公众号、少数派等平台

模块化重构版本 v2.0.0
"""

import asyncio
import sys

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.exceptions import CrawlerException
from app.api.router import api_router
from app.plugins.registry import initialize_plugins

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


app = FastAPI(
    title="OpenCrawler API",
    description="""
## 多平台网页 Markdown 提取 API

基于 FastAPI + Playwright 的网页内容提取服务，支持多种平台：

### 支持的平台
- **GitHub** - 仓库 README、文档等
- **知乎** - 文章、回答
- **小红书** - 笔记内容
- **微信公众号** - 文章内容
- **少数派** - 文章内容
- **通用网站** - 任意网页内容

### 特性
- 🚀 插件化架构，易于扩展
- 📝 自动转换为 Markdown 格式
- 🖼️ 支持图片下载和本地化
- 🔐 支持 Cookie 认证
- 🌐 RESTful API 接口
""",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")
    version: str = Field(..., description="API 版本")


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化插件"""
    await initialize_plugins()
    print(f"[OpenCrawler] 服务启动，监听 {settings.host}:{settings.port}")


@app.exception_handler(CrawlerException)
async def crawler_exception_handler(request: Request, exc: CrawlerException):
    """处理爬虫异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.get("/api/v1/health", response_model=HealthResponse, tags=["系统"])
async def health_check():
    """
    健康检查
    
    检查服务是否正常运行
    """
    return {
        "status": "healthy",
        "service": "OpenCrawler",
        "version": "2.0.0",
    }


app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )

"""
API 路由模块

注册所有 API 路由
"""

from fastapi import APIRouter

from app.api import pages, articles

api_router = APIRouter()

api_router.include_router(pages.router, prefix="/api/v1", tags=["页面"])
api_router.include_router(articles.router, prefix="/api/v1", tags=["文章"])

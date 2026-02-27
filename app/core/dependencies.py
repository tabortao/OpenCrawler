"""
依赖注入模块

提供 FastAPI 依赖注入功能
"""

from typing import Optional

from fastapi import Depends, Request

from app.core.config import Settings, settings
from app.core.exceptions import AuthenticationError


def get_settings() -> Settings:
    """获取应用配置"""
    return settings


def get_request_url(request: Request) -> str:
    """获取请求 URL"""
    return str(request.url)


class CommonQueryParams:
    """通用查询参数"""
    
    def __init__(
        self,
        url: str,
        download_images: bool = False,
    ):
        self.url = url
        self.download_images = download_images


def validate_url(url: str) -> str:
    """
    验证 URL 格式
    
    Args:
        url: 要验证的 URL
    
    Returns:
        验证通过的 URL
    
    Raises:
        URLValidationError: URL 格式不正确
    """
    from app.utils.url import is_valid_url
    from app.core.exceptions import URLValidationError
    
    if not is_valid_url(url):
        raise URLValidationError(
            message="URL 格式不正确，请提供有效的 HTTP/HTTPS URL",
            url=url,
        )
    
    return url


def check_platform_auth(platform: str, settings: Settings = Depends(get_settings)) -> None:
    """
    检查平台认证状态
    
    Args:
        platform: 平台名称
        settings: 应用配置
    
    Raises:
        AuthenticationError: 需要认证但未配置 Cookie
    """
    config = settings.get_platform_config(platform)
    
    if config.requires_auth:
        cookie = settings.get_cookie(platform)
        if not cookie:
            raise AuthenticationError(
                message=f"{platform} 平台需要登录，请配置 Cookie",
                platform=platform,
            )

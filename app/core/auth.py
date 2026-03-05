"""
认证模块

提供 API 令牌验证功能
"""

import os
import secrets
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader

from app.core.config import settings


logger = logging.getLogger(__name__)

security_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Token", auto_error=False)


class AuthError(HTTPException):
    """认证错误"""
    
    def __init__(self, detail: str = "无效的认证凭据"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_token(length: int = 32) -> str:
    """
    生成高强度随机令牌
    
    Args:
        length: 令牌长度（字节数）
    
    Returns:
        随机令牌字符串
    """
    return secrets.token_urlsafe(length)


def verify_token(provided_token: Optional[str]) -> bool:
    """
    验证令牌是否有效
    
    Args:
        provided_token: 提供的令牌
    
    Returns:
        是否有效
    """
    if not provided_token:
        return False
    
    expected_token = settings.api_token
    
    if not expected_token:
        logger.warning("API_TOKEN 未配置，拒绝所有请求")
        return False
    
    return secrets.compare_digest(provided_token, expected_token)


async def get_current_token(
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    api_key: Optional[str] = Depends(api_key_header),
) -> str:
    """
    从请求中提取令牌
    
    支持两种认证方式：
    1. Bearer Token: Authorization: Bearer <token>
    2. API Key Header: X-API-Token: <token>
    
    Args:
        bearer_credentials: Bearer 认证凭据
        api_key: API Key 头
    
    Returns:
        令牌字符串
    
    Raises:
        AuthError: 认证失败
    """
    token = None
    
    if bearer_credentials:
        token = bearer_credentials.credentials
    elif api_key:
        token = api_key
    
    if not token:
        raise AuthError("缺少认证令牌，请在请求头中提供 Authorization: Bearer <token> 或 X-API-Token: <token>")
    
    if not verify_token(token):
        raise AuthError("无效的认证令牌")
    
    return token


async def verify_api_auth(
    token: str = Depends(get_current_token),
) -> bool:
    """
    验证 API 认证
    
    用作 FastAPI 依赖项
    
    Args:
        token: 已验证的令牌
    
    Returns:
        认证成功返回 True
    """
    return True


def is_auth_enabled() -> bool:
    """
    检查是否启用了认证
    
    Returns:
        是否启用了认证
    """
    return bool(settings.api_token)


class OptionalAuthDependency:
    """
    可选认证依赖类
    
    如果配置了 API_TOKEN，则验证令牌；否则跳过验证
    """
    
    async def __call__(self, request: Request) -> bool:
        if not is_auth_enabled():
            return True
        
        bearer_credentials = await security_bearer(request)
        api_key = await api_key_header(request)
        
        token = None
        if bearer_credentials:
            token = bearer_credentials.credentials
        elif api_key:
            token = api_key
        
        if not token:
            raise AuthError("缺少认证令牌，请在请求头中提供 Authorization: Bearer <token> 或 X-API-Token: <token>")
        
        if not verify_token(token):
            raise AuthError("无效的认证令牌")
        
        return True


optional_auth = OptionalAuthDependency()

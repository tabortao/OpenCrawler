"""
异常定义模块

定义应用程序中使用的所有自定义异常
"""

from typing import Optional


class CrawlerException(Exception):
    """爬虫异常基类"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "CRAWLER_ERROR",
        status_code: int = 500,
        details: Optional[dict] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class URLValidationError(CrawlerException):
    """URL 验证错误"""
    
    def __init__(self, message: str = "URL 格式不正确", url: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="INVALID_URL",
            status_code=400,
            details={"url": url} if url else {},
        )


class ContentExtractionError(CrawlerException):
    """内容提取错误"""
    
    def __init__(
        self,
        message: str = "无法提取页面内容",
        url: Optional[str] = None,
        platform: Optional[str] = None,
    ):
        details = {}
        if url:
            details["url"] = url
        if platform:
            details["platform"] = platform
        super().__init__(
            message=message,
            error_code="CONTENT_ERROR",
            status_code=422,
            details=details,
        )


class AuthenticationError(CrawlerException):
    """认证错误"""
    
    def __init__(
        self,
        message: str = "需要登录或 Cookie 已过期",
        platform: Optional[str] = None,
    ):
        details = {}
        if platform:
            details["platform"] = platform
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_REQUIRED",
            status_code=401,
            details=details,
        )


class TimeoutError(CrawlerException):
    """超时错误"""
    
    def __init__(
        self,
        message: str = "请求超时",
        url: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ):
        details = {}
        if url:
            details["url"] = url
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(
            message=message,
            error_code="TIMEOUT",
            status_code=504,
            details=details,
        )


class PluginNotFoundError(CrawlerException):
    """插件未找到错误"""
    
    def __init__(self, plugin_name: str):
        super().__init__(
            message=f"插件 '{plugin_name}' 未找到",
            error_code="PLUGIN_NOT_FOUND",
            status_code=404,
            details={"plugin_name": plugin_name},
        )


class PlatformNotSupportedError(CrawlerException):
    """平台不支持错误"""
    
    def __init__(self, platform: str):
        super().__init__(
            message=f"平台 '{platform}' 不支持",
            error_code="PLATFORM_NOT_SUPPORTED",
            status_code=400,
            details={"platform": platform},
        )


class ImageDownloadError(CrawlerException):
    """图片下载错误"""
    
    def __init__(
        self,
        message: str = "图片下载失败",
        url: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_code="IMAGE_DOWNLOAD_ERROR",
            status_code=500,
            details={"url": url} if url else {},
        )


class ConfigurationError(CrawlerException):
    """配置错误"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=details,
        )

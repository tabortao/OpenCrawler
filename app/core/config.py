"""
配置管理模块

提供应用程序配置的集中管理，支持环境变量加载
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class PlatformConfig:
    """平台配置"""
    selector: str
    timeout: int = 15000
    scroll_times: int = 2
    requires_auth: bool = False
    cookie_env_key: Optional[str] = None


@dataclass
class Settings:
    """应用程序配置"""
    
    host: str = "127.0.0.1"
    port: int = 8000
    output_dir: str = "output"
    proxy_url: str = ""
    
    zhihu_cookie: str = ""
    xhs_cookie: str = ""
    
    api_token: str = ""
    
    browser_headless: bool = True
    browser_timeout: int = 45000
    browser_navigation_timeout: int = 60000
    
    api_timeout: int = 300
    
    platforms: dict[str, PlatformConfig] = field(default_factory=dict)
    
    def __post_init__(self):
        self.host = os.getenv("HOST", self.host)
        self.port = int(os.getenv("PORT", str(self.port)))
        self.output_dir = os.getenv("OUTPUT_DIR", self.output_dir)
        self.proxy_url = os.getenv("PROXY_URL", self.proxy_url)
        self.zhihu_cookie = os.getenv("ZHIHU_COOKIE", self.zhihu_cookie)
        self.xhs_cookie = os.getenv("XHS_COOKIE", self.xhs_cookie)
        self.api_token = os.getenv("API_TOKEN", self.api_token)
        
        if os.getenv("BROWSER_HEADLESS"):
            self.browser_headless = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
        
        self._init_platform_configs()
    
    def _init_platform_configs(self):
        """初始化平台配置"""
        self.platforms = {
            "github": PlatformConfig(
                selector=".markdown-body",
                timeout=15000,
                scroll_times=0,
                requires_auth=False,
            ),
            "zhihu": PlatformConfig(
                selector=".Post-RichText, .RichText, .RichContent-inner",
                timeout=20000,
                scroll_times=3,
                requires_auth=True,
                cookie_env_key="ZHIHU_COOKIE",
            ),
            "xiaohongshu": PlatformConfig(
                selector=".note-content, #detail-desc",
                timeout=20000,
                scroll_times=3,
                requires_auth=True,
                cookie_env_key="XHS_COOKIE",
            ),
            "wechat": PlatformConfig(
                selector=".rich_media_content",
                timeout=15000,
                scroll_times=2,
                requires_auth=False,
            ),
            "sspai": PlatformConfig(
                selector="article, .article-content, .content",
                timeout=15000,
                scroll_times=3,
                requires_auth=False,
            ),
            "generic": PlatformConfig(
                selector="article, .content, .post, main",
                timeout=15000,
                scroll_times=2,
                requires_auth=False,
            ),
        }
    
    def get_platform_config(self, platform: str) -> PlatformConfig:
        """
        获取指定平台的配置
        
        Args:
            platform: 平台名称
        
        Returns:
            平台配置对象
        """
        return self.platforms.get(platform, self.platforms["generic"])
    
    def get_cookie(self, platform: str) -> str:
        """
        获取指定平台的 Cookie
        
        Args:
            platform: 平台名称
        
        Returns:
            Cookie 字符串
        """
        config = self.get_platform_config(platform)
        if config.cookie_env_key:
            return os.getenv(config.cookie_env_key, "")
        return ""
    
    def get_browser_args(self) -> dict:
        """
        获取浏览器启动参数
        
        Returns:
            浏览器参数字典
        """
        args: dict = {
            "headless": self.browser_headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-sync",
                "--disable-translate",
                "--disable-default-apps",
                "--mute-audio",
                "--no-first-run",
            ],
        }
        
        if self.proxy_url:
            args["proxy"] = {"server": self.proxy_url}
        
        return args


settings = Settings()

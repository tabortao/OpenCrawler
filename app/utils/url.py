"""
URL 工具模块

提供 URL 验证、平台检测、Cookie 解析等功能
"""

import re
from typing import Any
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """
    验证 URL 格式是否正确
    
    Args:
        url: 要验证的 URL
    
    Returns:
        URL 是否有效
    """
    if not url or not url.strip():
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def detect_platform(url: str) -> str:
    """
    检测 URL 所属平台
    
    Args:
        url: 要检测的 URL
    
    Returns:
        平台名称
    """
    url_lower = url.lower()
    
    if "github.com" in url_lower:
        return "github"
    elif "zhihu.com" in url_lower:
        return "zhihu"
    elif "xiaohongshu.com" in url_lower or "xhslink.com" in url_lower:
        return "xiaohongshu"
    elif "mp.weixin.qq.com" in url_lower:
        return "wechat"
    elif "sspai.com" in url_lower:
        return "sspai"
    elif "toutiao.com" in url_lower:
        return "toutiao"
    else:
        return "generic"


def parse_cookie_string(cookie_string: str) -> list[dict[str, Any]]:
    """
    解析 Cookie 字符串为字典列表
    
    Args:
        cookie_string: Cookie 字符串，格式为 "name1=value1; name2=value2"
    
    Returns:
        Cookie 字典列表
    """
    if not cookie_string or not cookie_string.strip():
        return []
    
    cookies = []
    pairs = cookie_string.split(";")
    
    for pair in pairs:
        pair = pair.strip()
        if not pair:
            continue
        
        if "=" in pair:
            name, value = pair.split("=", 1)
            cookies.append({
                "name": name.strip(),
                "value": value.strip(),
                "domain": "",
                "path": "/",
            })
    
    return cookies


def normalize_url(url: str) -> str:
    """
    标准化 URL
    
    Args:
        url: 要标准化的 URL
    
    Returns:
        标准化后的 URL
    """
    url = url.strip()
    
    if url.startswith("//"):
        url = "https:" + url
    
    return url


def get_url_domain(url: str) -> str:
    """
    获取 URL 的域名
    
    Args:
        url: URL 字符串
    
    Returns:
        域名
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return ""


def is_short_url(url: str) -> bool:
    """
    判断是否为短链接
    
    Args:
        url: URL 字符串
    
    Returns:
        是否为短链接
    """
    short_url_domains = [
        "xhslink.com",
        "t.cn",
        "bit.ly",
        "goo.gl",
        "tinyurl.com",
    ]
    
    domain = get_url_domain(url).lower()
    return any(short_domain in domain for short_domain in short_url_domains)

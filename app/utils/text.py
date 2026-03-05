"""
文本处理工具模块

提供 Markdown 清理、HTML 标题提取等文本处理功能
"""

import re
from typing import Optional


def clean_markdown(markdown: str) -> str:
    """
    清理 Markdown 内容
    
    Args:
        markdown: Markdown 内容
    
    Returns:
        清理后的 Markdown 内容
    """
    if not markdown:
        return ""
    
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = markdown.strip()
    
    return markdown


def extract_title_from_html(html: str) -> str:
    """
    从 HTML 内容中提取标题
    
    支持多种标题提取方式：
    1. og:title meta 标签
    2. twitter:title meta 标签
    3. 微信公众号 activity-name 元素
    4. h1 标签
    5. title 标签
    
    Args:
        html: HTML 内容
    
    Returns:
        标题文本
    """
    if not html:
        return ""
    
    og_title_match = re.search(
        r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE
    )
    if og_title_match:
        title = og_title_match.group(1).strip()
        if title:
            return _clean_title(title)
    
    og_title_match2 = re.search(
        r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:title["\']',
        html,
        re.IGNORECASE
    )
    if og_title_match2:
        title = og_title_match2.group(1).strip()
        if title:
            return _clean_title(title)
    
    twitter_title_match = re.search(
        r'<meta[^>]*name=["\']twitter:title["\'][^>]*content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE
    )
    if twitter_title_match:
        title = twitter_title_match.group(1).strip()
        if title:
            return _clean_title(title)
    
    activity_name_match = re.search(
        r'id=["\']activity-name["\'][^>]*>([^<]+)<',
        html,
        re.IGNORECASE
    )
    if activity_name_match:
        title = activity_name_match.group(1).strip()
        if title:
            return _clean_title(title)
    
    activity_name_match2 = re.search(
        r'<[^>]*id=["\']activity-name["\'][^>]*>([^<]+)<',
        html,
        re.IGNORECASE
    )
    if activity_name_match2:
        title = activity_name_match2.group(1).strip()
        if title:
            return _clean_title(title)
    
    h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
    if h1_match:
        title = h1_match.group(1).strip()
        if title and len(title) > 2:
            return _clean_title(title)
    
    title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
        if title:
            return _clean_title(title)
    
    return ""


def _clean_title(title: str) -> str:
    """
    清理标题
    
    Args:
        title: 原始标题
    
    Returns:
        清理后的标题
    """
    if not title:
        return ""
    
    title = re.sub(r'\s+', ' ', title)
    title = title.strip()
    
    # 只移除特定的网站后缀，不要使用太宽泛的规则
    suffixes_to_remove = [
        r'\s*[-_|]\s*微信公众平台\s*$',
        r'\s*[-_|]\s*微信\s*$',
        r'\s*[-_|]\s*知乎\s*$',
        r'\s*[-_|]\s*少数派\s*$',
        r'\s*[-_|]\s*GitHub\s*$',
        r'\s*[-_|]\s*小红书\s*$',
        r'\s*[-_|]\s*CSDN\s*$',
        r'\s*[-_|]\s*掘金\s*$',
        r'\s*[-_|]\s*简书\s*$',
        r'\s*[-_|]\s*博客园\s*$',
        r'\s*[-_|]\s*思否\s*$',
        r'\s*[-_|]\s*SegmentFault\s*$',
        r'\s*[-_|]\s*今日头条\s*$',
        r'\s*[-_|]\s*搜狐\s*$',
        r'\s*[-_|]\s*网易\s*$',
        r'\s*[-_|]\s*新浪\s*$',
        r'\s*[-_|]\s*腾讯\s*$',
        r'\s*[-_|]\s*百度\s*$',
        r'\s*_\s*微信公众号\s*$',
        r'\s*\|\s*微信公众号\s*$',
    ]
    
    for suffix in suffixes_to_remove:
        title = re.sub(suffix, '', title, flags=re.IGNORECASE)
    
    return title.strip()


def remove_duplicate_lines(text: str) -> str:
    """
    移除重复的行
    
    Args:
        text: 文本内容
    
    Returns:
        处理后的文本
    """
    if not text:
        return ""
    
    lines = text.split("\n")
    seen = set()
    result = []
    
    for line in lines:
        stripped = line.strip()
        if stripped and stripped in seen:
            continue
        if stripped:
            seen.add(stripped)
        result.append(line)
    
    return "\n".join(result)


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀
    
    Returns:
        截断后的文本
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def normalize_whitespace(text: str) -> str:
    """
    标准化空白字符
    
    Args:
        text: 原始文本
    
    Returns:
        标准化后的文本
    """
    if not text:
        return ""
    
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    return text.strip()


def clean_zhihu_title(title: str) -> str:
    """
    清理知乎标题中的私信提示
    
    Args:
        title: 原始标题
    
    Returns:
        清理后的标题
    """
    if not title:
        return ""
    
    patterns = [
        r'\s*[\(（]\s*\d+\s*封私信.*?[\)）]',
        r'\s*[\(（]\s*\d+\s*条消息.*?[\)）]',
        r'\s*-\s*\d+\s*封私信.*',
        r'\s*\d+\s*封私信',
        r'\s*\d+\s*条消息',
    ]
    
    for pattern in patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    
    return title.strip()


def remove_html_entities(text: str) -> str:
    """
    移除 HTML 实体
    
    Args:
        text: 包含 HTML 实体的文本
    
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    import html
    text = html.unescape(text)
    
    replacements = {
        '&nbsp;': ' ',
        '&copy;': '©',
        '&reg;': '®',
        '&trade;': '™',
        '&hellip;': '…',
        '&mdash;': '—',
        '&ndash;': '–',
    }
    
    for entity, char in replacements.items():
        text = text.replace(entity, char)
    
    return text

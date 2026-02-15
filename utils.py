import re
from typing import Any
from urllib.parse import urlparse


def parse_cookie_string(cookie_string: str) -> list[dict[str, Any]]:
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


def is_valid_url(url: str) -> bool:
    if not url or not url.strip():
        return False

    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def detect_platform(url: str) -> str:
    url_lower = url.lower()

    if "github.com" in url_lower:
        return "github"
    elif "zhihu.com" in url_lower:
        return "zhihu"
    elif "xiaohongshu.com" in url_lower or "xhslink.com" in url_lower:
        return "xiaohongshu"
    elif "mp.weixin.qq.com" in url_lower:
        return "wechat"
    else:
        return "generic"


def get_platform_config(platform: str) -> dict[str, Any]:
    configs = {
        "github": {
            "selector": ".markdown-body",
            "timeout": 15000,
            "scroll_times": 0,
        },
        "zhihu": {
            "selector": ".Post-RichText, .RichText, .RichContent-inner",
            "timeout": 20000,
            "scroll_times": 3,
        },
        "xiaohongshu": {
            "selector": ".note-content, #detail-desc",
            "timeout": 20000,
            "scroll_times": 3,
        },
        "wechat": {
            "selector": ".rich_media_content",
            "timeout": 15000,
            "scroll_times": 2,
        },
        "generic": {
            "selector": "article, .content, .post, main",
            "timeout": 15000,
            "scroll_times": 2,
        },
    }

    return configs.get(platform, configs["generic"])


def clean_markdown(markdown: str) -> str:
    if not markdown:
        return ""

    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = markdown.strip()

    return markdown


def extract_title_from_html(html: str) -> str:
    if not html:
        return ""

    title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
        title = re.sub(r"\s*[-_|]\s*.*$", "", title)
        return title

    return ""


def sanitize_filename(filename: str) -> str:
    if not filename:
        return ""

    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    filename = re.sub(r"\s+", "_", filename)
    filename = filename.strip("._")

    if len(filename) > 100:
        filename = filename[:100]

    return filename

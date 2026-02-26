"""
Markdown 转换模块

提供 HTML 到 Markdown 的转换功能，支持多平台优化处理。
"""

import re
from typing import Optional

from bs4 import BeautifulSoup
from markdownify import markdownify as md


def convert_html_to_markdown(
    html: str,
    platform: str = "generic",
    strip_scripts: bool = True,
    strip_styles: bool = True,
) -> str:
    """
    将 HTML 内容转换为 Markdown 格式
    
    Args:
        html: 要转换的 HTML 内容
        platform: 目标平台（wechat/zhihu/xiaohongshu/generic）
        strip_scripts: 是否移除 script 标签
        strip_styles: 是否移除 style 标签
    
    Returns:
        转换后的 Markdown 文本
    """
    if not html or not html.strip():
        return ""
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 移除脚本标签
    if strip_scripts:
        for script in soup.find_all("script"):
            script.decompose()
    
    # 移除样式标签
    if strip_styles:
        for style in soup.find_all("style"):
            style.decompose()
    
    # 移除 HTML 注释
    for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith("<!--")):
        comment.extract()
    
    # 根据平台进行特殊处理
    if platform == "wechat":
        _process_wechat_images(soup)
        _process_wechat_br(soup)
    elif platform == "zhihu":
        _process_zhihu_content(soup)
    elif platform == "xiaohongshu":
        _process_xiaohongshu_content(soup)
    
    # 转换为 Markdown
    markdown = md(
        str(soup),
        heading_style="atx",
        bullets="-",
        strip=["script", "style", "nav", "header", "footer"],
        escape_asterisks=False,
        escape_underscores=False,
    )
    
    # 清理格式
    markdown = _clean_markdown(markdown)
    
    return markdown


def _process_wechat_images(soup: BeautifulSoup) -> None:
    """
    处理微信公众号图片
    
    将 data-src 属性转换为 src 属性，移除其他无用属性
    """
    for img in soup.find_all("img"):
        data_src = img.get("data-src")
        if data_src:
            img["src"] = data_src
            del img["data-src"]
        
        # 只保留 src, alt, title 属性
        for attr in list(img.attrs.keys()):
            if attr not in ["src", "alt", "title"]:
                del img[attr]


def _process_wechat_br(soup: BeautifulSoup) -> None:
    """
    处理微信公众号换行标签
    
    将 br 标签替换为换行符
    """
    for br in soup.find_all("br"):
        br.replace_with("\n")


def _process_zhihu_content(soup: BeautifulSoup) -> None:
    """
    处理知乎内容
    
    移除导航、按钮等非正文元素
    """
    # 移除导航和头部
    for nav in soup.find_all(["nav", "header"]):
        nav.decompose()
    
    # 移除按钮
    for button in soup.find_all("button"):
        button.decompose()
    
    # 移除按钮样式的链接
    for a in soup.find_all("a"):
        if a.get("class") and any("Button" in c for c in a.get("class", [])):
            a.decompose()


def _process_xiaohongshu_content(soup: BeautifulSoup) -> None:
    """
    处理小红书内容
    
    展开 span 标签，保留笔记文本内容
    """
    for span in soup.find_all("span"):
        if span.get("class") and any("note-text" in c for c in span.get("class", [])):
            continue
        span.unwrap()


def _clean_markdown(markdown: str) -> str:
    """
    清理 Markdown 内容，处理格式问题
    
    包括：修复错误标题、移除多余空行、清理空白字符
    """
    if not markdown:
        return ""
    
    # 修复被错误识别的标题
    markdown = _fix_false_headings(markdown)
    
    # 移除多余空行
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    
    # 清理行首行尾空白
    markdown = re.sub(r"^\s+|\s+$", "", markdown, flags=re.MULTILINE)
    markdown = markdown.strip()
    
    # 合并连续空行
    lines = markdown.split("\n")
    cleaned_lines = []
    prev_empty = False
    
    for line in lines:
        is_empty = not line.strip()
        if is_empty and prev_empty:
            continue
        cleaned_lines.append(line)
        prev_empty = is_empty
    
    return "\n".join(cleaned_lines)


def _fix_false_headings(markdown: str) -> str:
    """
    修复被错误识别为标题的内容
    
    例如：小红书标签 #xxx[话题]# 不应被识别为标题
    """
    if not markdown:
        return ""
    
    # 处理小红书话题标签：#xxx[话题]# -> `#xxx[话题]#`
    xhs_tag_pattern = r'(#([^#\[\]]+)\[话题\]#)'
    markdown = re.sub(xhs_tag_pattern, r'`\1`', markdown)
    
    # 处理以 # 结尾的假标题（如 #xxx# 格式）
    false_heading_pattern = r'^(#{1,6})\s*([^#\n]*?)\s*#\s*$'
    
    def fix_heading(match):
        hashes = match.group(1)
        content = match.group(2).strip()
        if content and not re.match(r'^\s*$', content):
            # 短内容且无标点符号，可能是标签而非标题
            if len(content) < 20 and not re.search(r'[。！？，、；：]', content):
                return f"`{hashes}{content}#`"
        return match.group(0)
    
    markdown = re.sub(false_heading_pattern, fix_heading, markdown, flags=re.MULTILINE)
    
    return markdown


def extract_images_from_html(html: str) -> list[str]:
    """
    从 HTML 内容中提取所有图片 URL
    
    Args:
        html: HTML 内容
    
    Returns:
        图片 URL 列表
    """
    if not html:
        return []
    
    soup = BeautifulSoup(html, "html.parser")
    image_urls = []
    
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src and not src.startswith("data:"):
            image_urls.append(src)
    
    return image_urls


def process_images_in_markdown(
    markdown: str,
    image_urls: list[str],
    image_downloader,
) -> str:
    """
    处理 Markdown 中的图片，下载并替换为本地路径
    
    Args:
        markdown: Markdown 内容
        image_urls: 图片 URL 列表
        image_downloader: 图片下载器实例
    
    Returns:
        处理后的 Markdown 内容
    """
    if not markdown:
        return markdown
    
    img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def replace_image_url(match):
        alt_text = match.group(1)
        img_url = match.group(2)
        
        if not img_url or img_url.startswith("data:") or img_url.startswith("images/"):
            return match.group(0)
        
        clean_url = img_url.replace("&amp;", "&")
        local_path = image_downloader.download_image(clean_url)
        
        if local_path:
            return f"![{alt_text}]({local_path})"
        return match.group(0)
    
    markdown = re.sub(img_pattern, replace_image_url, markdown)
    
    return markdown

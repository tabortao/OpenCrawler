"""
Markdown 转换模块

提供 HTML 到 Markdown 的转换功能，支持多平台优化处理。
参考 article-downloader 项目的实现进行优化。
"""

import html
import re
from typing import Optional

from bs4 import BeautifulSoup, NavigableString, Tag


def html_unescape(text: str) -> str:
    """
    HTML 实体解码
    
    将 HTML 实体转换为对应的字符
    """
    if not text:
        return ""
    
    text = html.unescape(text)
    
    replacements = {
        '&nbsp;': ' ',
        '&copy;': '©',
        '&reg;': '®',
        '&trade;': '™',
        '&hellip;': '…',
        '&mdash;': '—',
        '&ndash;': '–',
        '&lsquo;': ''',
        '&rsquo;': ''',
        '&ldquo;': '"',
        '&rdquo;': '"',
    }
    
    for entity, char in replacements.items():
        text = text.replace(entity, char)
    
    return text


def convert_html_to_markdown(
    html_content: str,
    platform: str = "generic",
    strip_scripts: bool = True,
    strip_styles: bool = True,
) -> str:
    """
    将 HTML 内容转换为 Markdown 格式
    
    Args:
        html_content: 要转换的 HTML 内容
        platform: 目标平台（wechat/zhihu/xiaohongshu/generic）
        strip_scripts: 是否移除 script 标签
        strip_styles: 是否移除 style 标签
    
    Returns:
        转换后的 Markdown 文本
    """
    if not html_content or not html_content.strip():
        return ""
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    if strip_scripts:
        for script in soup.find_all("script"):
            script.decompose()
    
    if strip_styles:
        for style in soup.find_all("style"):
            style.decompose()
    
    for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith("<!--")):
        comment.extract()
    
    for noscript in soup.find_all("noscript"):
        noscript.decompose()
    
    if platform == "wechat":
        _process_wechat_content(soup)
    elif platform == "zhihu":
        _process_zhihu_content(soup)
    elif platform == "xiaohongshu":
        _process_xiaohongshu_content(soup)
    
    markdown = _convert_element_to_markdown(soup, platform)
    
    markdown = _clean_markdown(markdown)
    
    return markdown


def _process_wechat_content(soup: BeautifulSoup) -> None:
    """
    处理微信公众号内容
    
    - 将 data-src 属性转换为 src 属性
    - 移除微信特定的无用标签和属性
    - 识别微信样式的标题（通过 span + textstyle + font-weight: bold）
    """
    imgs = list(soup.find_all("img"))
    
    for img in imgs:
        data_src = img.get("data-src", "")
        src = img.get("src", "")
        
        valid_data_src = data_src and not data_src.startswith("data:") and data_src != "..." and len(data_src) > 10
        valid_src = src and not src.startswith("data:") and src != "..." and len(src) > 10
        
        if valid_data_src:
            img["src"] = data_src
        elif valid_src:
            pass
        else:
            img.decompose()
            continue
        
        for attr in list(img.attrs.keys()):
            if attr not in ["src", "alt", "title"]:
                del img[attr]
    
    for br in soup.find_all("br"):
        br.replace_with("\n")
    
    for tag in soup.find_all(["mp-style-type", "mp-common-profile", "mpvideosnap"]):
        tag.decompose()
    
    for tag in soup.find_all(class_=["js_video_play", "video_iframe", "rich_media_video"]):
        tag.decompose()
    
    _convert_wechat_style_headings(soup)
    
    for span in soup.find_all("span"):
        if not span.get_text(strip=True) and not span.find_all("img"):
            span.decompose()
    
    for tag in soup.find_all(id=["js_content_video", "js_player"]):
        tag.decompose()


def _convert_wechat_style_headings(soup: BeautifulSoup) -> None:
    """
    将微信样式的标题转换为标准 HTML 标题
    
    微信公众号中，标题通常通过 span 标签实现，特征：
    - 有 textstyle 属性
    - style 包含 font-weight: bold
    - font-size 通常比正文大（17px vs 15px）
    """
    spans = list(soup.find_all("span"))
    
    for span in spans:
        textstyle = span.get("textstyle")
        style = span.get("style", "")
        
        if textstyle is not None and "font-weight" in style and "bold" in style:
            text = span.get_text(strip=True)
            
            if len(text) < 2 or len(text) > 100:
                continue
            
            font_size_match = re.search(r'font-size:\s*(\d+)px', style)
            font_size = int(font_size_match.group(1)) if font_size_match else 0
            
            if font_size >= 17:
                h2_tag = soup.new_tag("h2")
                h2_tag.string = text
                span.replace_with(h2_tag)
            elif font_size >= 16:
                h3_tag = soup.new_tag("h3")
                h3_tag.string = text
                span.replace_with(h3_tag)


def _process_zhihu_content(soup: BeautifulSoup) -> None:
    """
    处理知乎内容
    
    移除导航、按钮等非正文元素
    """
    for nav in soup.find_all(["nav", "header"]):
        nav.decompose()
    
    for button in soup.find_all("button"):
        button.decompose()
    
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


def _convert_element_to_markdown(element, platform: str = "generic") -> str:
    """
    递归转换 HTML 元素为 Markdown
    
    这是核心转换函数，处理各种 HTML 标签
    """
    if isinstance(element, NavigableString):
        text = str(element)
        text = html_unescape(text)
        return text
    
    if not isinstance(element, Tag):
        return ""
    
    tag_name = element.name.lower()
    
    if tag_name in ["script", "style", "noscript", "nav", "header", "footer"]:
        return ""
    
    children_text = ""
    for child in element.children:
        children_text += _convert_element_to_markdown(child, platform)
    
    if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        level = int(tag_name[1])
        content = children_text.strip()
        if content:
            return f"\n\n{'#' * level} {content}\n\n"
        return ""
    
    elif tag_name == "p":
        content = children_text.strip()
        if content:
            return f"\n\n{content}\n\n"
        return ""
    
    elif tag_name in ["strong", "b"]:
        content = children_text.strip()
        if content:
            return f"**{content}**"
        return ""
    
    elif tag_name in ["em", "i"]:
        content = children_text.strip()
        if content:
            return f"*{content}*"
        return ""
    
    elif tag_name == "code":
        content = children_text
        if content:
            if '\n' in content or len(content) > 50:
                return f"\n\n```\n{content}\n```\n\n"
            return f"`{content}`"
        return ""
    
    elif tag_name == "pre":
        code_tag = element.find("code")
        if code_tag:
            content = code_tag.get_text()
        else:
            content = children_text.strip()
        
        if content:
            lang = ""
            if code_tag and code_tag.get("class"):
                for cls in code_tag.get("class", []):
                    if cls.startswith("language-"):
                        lang = cls[9:]
                        break
            content = content.strip()
            return f"\n\n```{lang}\n{content}\n```\n\n"
        return ""
    
    elif tag_name == "a":
        href = element.get("href", "")
        content = children_text.strip()
        if content and href and not href.startswith("javascript:"):
            href = html_unescape(href)
            return f"[{content}]({href})"
        return content
    
    elif tag_name == "img":
        src = element.get("src") or element.get("data-src", "")
        alt = element.get("alt", "图片")
        if src:
            src = html_unescape(src)
            if src.startswith("//"):
                src = "https:" + src
            return f"\n\n![{alt}]({src})\n\n"
        return ""
    
    elif tag_name == "br":
        return "\n"
    
    elif tag_name == "hr":
        return "\n\n---\n\n"
    
    elif tag_name in ["ul", "ol"]:
        items = []
        for i, li in enumerate(element.find_all("li", recursive=False)):
            item_content = _convert_element_to_markdown(li, platform).strip()
            if item_content:
                if tag_name == "ol":
                    items.append(f"{i + 1}. {item_content}")
                else:
                    items.append(f"- {item_content}")
        if items:
            return "\n\n" + "\n".join(items) + "\n\n"
        return ""
    
    elif tag_name == "li":
        return children_text
    
    elif tag_name == "blockquote":
        content = children_text.strip()
        if content:
            lines = content.split("\n")
            quoted_lines = [f"> {line.strip()}" for line in lines if line.strip()]
            return "\n\n" + "\n".join(quoted_lines) + "\n\n"
        return ""
    
    elif tag_name == "table":
        return _convert_table_to_markdown(element)
    
    elif tag_name in ["div", "section", "article", "main"]:
        return children_text
    
    elif tag_name == "span":
        return children_text
    
    else:
        return children_text


def _convert_table_to_markdown(table: Tag) -> str:
    """
    将 HTML 表格转换为 Markdown 表格
    """
    rows = table.find_all("tr")
    if not rows:
        return ""
    
    md_rows = []
    header_row = None
    
    thead = table.find("thead")
    if thead:
        header_cells = thead.find_all(["th", "td"])
        if header_cells:
            header_row = [cell.get_text(strip=True) for cell in header_cells]
    
    for row in rows:
        cells = row.find_all(["th", "td"])
        if cells:
            cell_texts = [cell.get_text(strip=True).replace("|", "\\|") for cell in cells]
            if not header_row and row.find("th"):
                header_row = cell_texts
            else:
                md_rows.append(cell_texts)
    
    if header_row:
        md_rows.insert(0, header_row)
    
    if not md_rows:
        return ""
    
    num_cols = max(len(row) for row in md_rows)
    
    result_rows = []
    for i, row in enumerate(md_rows):
        while len(row) < num_cols:
            row.append("")
        result_rows.append("| " + " | ".join(row) + " |")
        
        if i == 0:
            separator = "| " + " | ".join(["---"] * num_cols) + " |"
            result_rows.append(separator)
    
    return "\n\n" + "\n".join(result_rows) + "\n\n"


def _clean_markdown(markdown: str) -> str:
    """
    清理 Markdown 内容，处理格式问题
    
    包括：HTML 解码、修复错误标题、移除多余空行、清理空白字符
    """
    if not markdown:
        return ""
    
    markdown = html_unescape(markdown)
    
    markdown = _fix_false_headings(markdown)
    
    markdown = _convert_chinese_section_to_heading(markdown)
    
    markdown = re.sub(r"\n{4,}", "\n\n\n", markdown)
    
    lines = markdown.split("\n")
    cleaned_lines = []
    prev_empty = False
    prev_was_heading = False
    
    for line in lines:
        is_empty = not line.strip()
        is_heading = line.strip().startswith("#")
        
        if is_empty and prev_empty:
            continue
        
        if is_heading and prev_was_heading and not prev_empty:
            cleaned_lines.append("")
        
        cleaned_lines.append(line)
        prev_empty = is_empty
        prev_was_heading = is_heading
    
    markdown = "\n".join(cleaned_lines)
    
    markdown = re.sub(r"^[ \t]+", "", markdown, flags=re.MULTILINE)
    markdown = re.sub(r"[ \t]+$", "", markdown, flags=re.MULTILINE)
    
    markdown = markdown.strip()
    
    return markdown


def _convert_chinese_section_to_heading(markdown: str) -> str:
    """
    将中文章节标题转换为 Markdown 标题
    
    识别模式：
    - 一、xxx -> ## 一、xxx
    - 二、xxx -> ## 二、xxx
    - 1.1 xxx -> ### 1.1 xxx
    - 2.1 xxx -> ### 2.1 xxx
    """
    if not markdown:
        return ""
    
    lines = markdown.split("\n")
    result_lines = []
    
    chinese_num_pattern = re.compile(r'^([一二三四五六七八九十]+)[、\.．]\s*(.+)$')
    decimal_num_pattern = re.compile(r'^(\d+\.\d+)\s+(.+)$')
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith("#"):
            result_lines.append(line)
            continue
        
        chinese_match = chinese_num_pattern.match(stripped)
        if chinese_match:
            result_lines.append(f"## {stripped}")
            continue
        
        decimal_match = decimal_num_pattern.match(stripped)
        if decimal_match:
            result_lines.append(f"### {stripped}")
            continue
        
        result_lines.append(line)
    
    return "\n".join(result_lines)


def _fix_false_headings(markdown: str) -> str:
    """
    修复被错误识别为标题的内容
    
    例如：小红书标签 #xxx[话题]# 不应被识别为标题
    """
    if not markdown:
        return ""
    
    xhs_tag_pattern = r'(#([^#\[\]]+)\[话题\]#)'
    markdown = re.sub(xhs_tag_pattern, r'`\1`', markdown)
    
    false_heading_pattern = r'^(#{1,6})\s*([^#\n]*?)\s*#\s*$'
    
    def fix_heading(match):
        hashes = match.group(1)
        content = match.group(2).strip()
        if content and not re.match(r'^\s*$', content):
            if len(content) < 20 and not re.search(r'[。！？，、；：]', content):
                return f"`{hashes}{content}#`"
        return match.group(0)
    
    markdown = re.sub(false_heading_pattern, fix_heading, markdown, flags=re.MULTILINE)
    
    return markdown


def extract_images_from_html(html_content: str) -> list[str]:
    """
    从 HTML 内容中提取所有图片 URL
    
    Args:
        html_content: HTML 内容
    
    Returns:
        图片 URL 列表
    """
    if not html_content:
        return []
    
    soup = BeautifulSoup(html_content, "html.parser")
    image_urls = []
    
    for img in soup.find_all("img"):
        data_src = img.get("data-src", "")
        src = img.get("src", "")
        
        src = data_src if data_src and not data_src.startswith("data:") else src
        
        if not src or src.startswith("data:"):
            continue
        
        if src == "..." or len(src) < 10:
            continue
        
        src = html_unescape(src)
        if src.startswith("//"):
            src = "https:" + src
        
        if src not in image_urls:
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


def generate_markdown_document(
    title: str,
    author: str = "",
    publish_time: str = "",
    content: str = "",
    source_url: str = "",
    tags: list[str] = None,
) -> str:
    """
    生成完整的 Markdown 文档
    
    文档结构：YAML 头部 -> 标题 -> 作者 -> 发布时间 -> 分隔线 -> 正文 -> 来源链接
    
    Args:
        title: 文章标题
        author: 作者名称
        publish_time: 发布时间
        content: 正文内容
        source_url: 原文链接
        tags: 标签列表
    
    Returns:
        完整的 Markdown 文档
    """
    tags_str = ", ".join(tags) if tags else "web-crawler"
    
    yaml_header = f"""---
title: {title}
url: {source_url}
date: {publish_time}
tags: [{tags_str}]
---

"""
    
    markdown = yaml_header
    markdown += f"# {title}\n\n"
    
    if author:
        markdown += f"**作者：** {author}\n\n"
    
    if publish_time:
        markdown += f"**发布时间：** {publish_time}\n\n"
    
    markdown += "---\n\n"
    
    if content:
        markdown += f"{content}\n\n"
    
    if source_url:
        markdown += "---\n\n"
        markdown += f"**来源：** [原文链接]({source_url})\n"
    
    return markdown

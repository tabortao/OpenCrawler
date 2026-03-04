"""
Markdown 转换器模块

提供 HTML 到 Markdown 的转换功能
"""

import html
import re
from typing import Optional

from bs4 import BeautifulSoup, NavigableString, Tag

from app.converters.base import BaseConverter, ConversionResult


class MarkdownConverter(BaseConverter):
    """
    Markdown 转换器
    
    将 HTML 内容转换为 Markdown 格式
    """
    
    @property
    def name(self) -> str:
        return "markdown"
    
    def convert(self, content: str, **kwargs) -> ConversionResult:
        """
        将 HTML 转换为 Markdown
        
        Args:
            content: HTML 内容
            **kwargs: 额外参数，支持 platform 参数
        
        Returns:
            转换结果
        """
        platform = kwargs.get("platform", "generic")
        markdown = self.convert_html_to_markdown(content, platform=platform)
        return ConversionResult(content=markdown, metadata={"platform": platform})
    
    @staticmethod
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
            platform: 目标平台
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
        
        MarkdownConverter._process_platform_content(soup, platform)
        
        markdown = MarkdownConverter._convert_element_to_markdown(soup, platform)
        
        markdown = MarkdownConverter._clean_markdown(markdown)
        
        return markdown
    
    @staticmethod
    def _process_platform_content(soup: BeautifulSoup, platform: str) -> None:
        """处理平台特定内容"""
        if platform == "wechat":
            MarkdownConverter._process_wechat_content(soup)
        elif platform == "zhihu":
            MarkdownConverter._process_zhihu_content(soup)
        elif platform == "xiaohongshu":
            MarkdownConverter._process_xiaohongshu_content(soup)
        elif platform == "sspai":
            MarkdownConverter._process_sspai_content(soup)
        elif platform == "toutiao":
            MarkdownConverter._process_toutiao_content(soup)
        elif platform == "generic":
            MarkdownConverter._process_generic_content(soup)
    
    @staticmethod
    def _process_generic_content(soup: BeautifulSoup) -> None:
        """处理通用网站内容"""
        img_data_attrs = [
            "data-original", "data-src", "data-lazy-src", "data-lazy",
            "data-url", "data-actualsrc", "data-image", "data-cover",
        ]
        
        imgs = list(soup.find_all("img"))
        
        for img in imgs:
            selected_src = None
            
            for attr in img_data_attrs:
                url = img.get(attr, "")
                if url and not url.startswith("data:") and url != "..." and len(url) > 10:
                    selected_src = url
                    break
            
            if not selected_src:
                srcset = img.get("srcset", "")
                if srcset:
                    parts = srcset.split(",")
                    if parts:
                        first_part = parts[0].strip().split()
                        if first_part:
                            selected_src = first_part[0]
            
            if not selected_src:
                src = img.get("src", "")
                if src and not src.startswith("data:") and src != "..." and len(src) > 10:
                    selected_src = src
            
            if not selected_src:
                img.decompose()
                continue
            
            if selected_src.startswith("//"):
                selected_src = "https:" + selected_src
            
            if "toutiao" not in selected_src.lower():
                if "?" in selected_src:
                    selected_src = selected_src.split("?")[0]
            
            img["src"] = selected_src
            
            for attr in list(img.attrs.keys()):
                if attr not in ["src", "alt", "title"]:
                    del img[attr]
        
        for tag in soup.find_all(["script", "style", "noscript"]):
            tag.decompose()
        
        remove_patterns = [
            r'\b(ad|advertisement|ads|adv|sponsor|promo)\b',
            r'\b(social|share|sharing|facebook|twitter|weibo|wechat)\b',
            r'\b(comment|comments|reply|replies)\b',
            r'\b(related|recommend|recommended|popular|trending)\b',
            r'\b(sidebar|widget|footer|header|nav|navigation|menu)\b',
            r'\b(newsletter|subscribe|subscription|rss)\b',
            r'\b(cookie|gdpr|privacy|consent)\b',
            r'\b(popup|modal|overlay|banner)\b',
        ]
        
        for pattern in remove_patterns:
            for tag in soup.find_all(class_=re.compile(pattern, re.I)):
                tag.decompose()
            for tag in soup.find_all(id=re.compile(pattern, re.I)):
                tag.decompose()
        
        for tag in soup.find_all(["nav", "aside", "footer"]):
            tag.decompose()
        
        for tag in soup.find_all(attrs={"aria-hidden": "true"}):
            if not tag.find_all(["img", "video", "audio"]):
                tag.decompose()
        
        for tag in soup.find_all(style=re.compile(r'display:\s*none|visibility:\s*hidden', re.I)):
            tag.decompose()
        
        for br in soup.find_all("br"):
            br.replace_with("\n")
        
        for hr in soup.find_all("hr"):
            hr.replace_with("\n\n---\n\n")
        
        MarkdownConverter._convert_style_headings(soup)
    
    @staticmethod
    def _convert_style_headings(soup: BeautifulSoup) -> None:
        """将样式标题转换为标准 HTML 标题"""
        spans = list(soup.find_all("span"))
        
        for span in spans:
            style = span.get("style", "")
            text = span.get_text(strip=True)
            
            if not text or len(text) < 2 or len(text) > 100:
                continue
            
            if "font-weight" in style and "bold" in style.lower():
                font_size_match = re.search(r'font-size:\s*(\d+)px', style)
                font_size = int(font_size_match.group(1)) if font_size_match else 0
                
                if font_size >= 18:
                    h2_tag = soup.new_tag("h2")
                    h2_tag.string = text
                    span.replace_with(h2_tag)
                elif font_size >= 16:
                    h3_tag = soup.new_tag("h3")
                    h3_tag.string = text
                    span.replace_with(h3_tag)
                elif font_size >= 14:
                    h4_tag = soup.new_tag("h4")
                    h4_tag.string = text
                    span.replace_with(h4_tag)
    
    @staticmethod
    def _process_wechat_content(soup: BeautifulSoup) -> None:
        """处理微信公众号内容"""
        imgs = list(soup.find_all("img"))
        
        for img in imgs:
            data_original = img.get("data-original", "")
            data_src = img.get("data-src", "")
            src = img.get("src", "")
            
            valid_data_original = data_original and not data_original.startswith("data:") and data_original != "..." and len(data_original) > 10
            valid_data_src = data_src and not data_src.startswith("data:") and data_src != "..." and len(data_src) > 10
            valid_src = src and not src.startswith("data:") and src != "..." and len(src) > 10
            
            if valid_data_original:
                img["src"] = data_original
            elif valid_data_src:
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
        
        MarkdownConverter._convert_wechat_style_headings(soup)
        
        for span in soup.find_all("span"):
            if not span.get_text(strip=True) and not span.find_all("img"):
                span.decompose()
        
        for tag in soup.find_all(id=["js_content_video", "js_player"]):
            tag.decompose()
    
    @staticmethod
    def _convert_wechat_style_headings(soup: BeautifulSoup) -> None:
        """将微信样式的标题转换为标准 HTML 标题"""
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
    
    @staticmethod
    def _process_zhihu_content(soup: BeautifulSoup) -> None:
        """处理知乎内容"""
        for nav in soup.find_all(["nav", "header"]):
            nav.decompose()
        
        for button in soup.find_all("button"):
            button.decompose()
        
        for a in soup.find_all("a"):
            if a.get("class") and any("Button" in c for c in a.get("class", [])):
                a.decompose()
    
    @staticmethod
    def _process_xiaohongshu_content(soup: BeautifulSoup) -> None:
        """处理小红书内容"""
        for span in soup.find_all("span"):
            if span.get("class") and any("note-text" in c for c in span.get("class", [])):
                continue
            span.unwrap()
    
    @staticmethod
    def _process_sspai_content(soup: BeautifulSoup) -> None:
        """处理少数派内容"""
        imgs = list(soup.find_all("img"))
        
        for img in imgs:
            data_original = img.get("data-original", "")
            src = img.get("src", "")
            
            check_url = data_original or src
            if check_url and ("avatar" in check_url.lower() or 
                              "/thumbnail/" in check_url.lower() or 
                              "!32x32" in check_url or "!72x72" in check_url or 
                              "!84x84" in check_url or "!100x100" in check_url or
                              "/avatar/" in check_url.lower()):
                img.decompose()
                continue
            
            if data_original and not data_original.startswith("data:") and len(data_original) > 10:
                if "?" in data_original:
                    data_original = data_original.split("?")[0]
                img["src"] = data_original
            elif src and not src.startswith("data:") and len(src) > 10:
                if "?" in src:
                    src = src.split("?")[0]
                img["src"] = src
            else:
                img.decompose()
                continue
            
            for attr in list(img.attrs.keys()):
                if attr not in ["src", "alt", "title"]:
                    del img[attr]
        
        for tag in soup.find_all(class_=["sidebar", "comments", "related-articles", "article__card"]):
            tag.decompose()
        
        for tag in soup.find_all(attrs={"data-v-cecd8240": True}):
            if tag.name in ["div", "section"] and not tag.get_text(strip=True):
                tag.decompose()
    
    @staticmethod
    def _process_toutiao_content(soup: BeautifulSoup) -> None:
        """处理今日头条内容"""
        imgs = list(soup.find_all("img"))
        
        for img in imgs:
            data_original = img.get("data-original", "")
            data_src = img.get("data-src", "")
            src = img.get("src", "")
            
            valid_data_original = data_original and not data_original.startswith("data:") and data_original != "..." and len(data_original) > 10
            valid_data_src = data_src and not data_src.startswith("data:") and data_src != "..." and len(data_src) > 10
            valid_src = src and not src.startswith("data:") and src != "..." and len(src) > 10
            
            if valid_data_original:
                img["src"] = data_original
            elif valid_data_src:
                img["src"] = data_src
            elif valid_src:
                pass
            else:
                img.decompose()
                continue
            
            # 确保 URL 是完整的
            if img["src"].startswith("//"):
                img["src"] = "https:" + img["src"]
            
            # 移除不需要的属性
            for attr in list(img.attrs.keys()):
                if attr not in ["src", "alt", "title"]:
                    del img[attr]
        
        # 移除不需要的元素
        for tag in soup.find_all(class_=["comments", "related-articles", "recommend", "advertisement"]):
            tag.decompose()
    
    @staticmethod
    def _convert_element_to_markdown(element, platform: str = "generic") -> str:
        """递归转换 HTML 元素为 Markdown"""
        if isinstance(element, NavigableString):
            text = str(element)
            text = html.unescape(text)
            return text
        
        if not isinstance(element, Tag):
            return ""
        
        tag_name = element.name.lower()
        
        if tag_name in ["script", "style", "noscript", "nav", "header", "footer"]:
            return ""
        
        children_text = ""
        for child in element.children:
            children_text += MarkdownConverter._convert_element_to_markdown(child, platform)
        
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
                href = html.unescape(href)
                return f"[{content}]({href})"
            return content
        
        elif tag_name == "img":
            # 尝试获取完整的图片 URL，包括查询参数
            src = element.get("data-original") or element.get("data-src") or element.get("src", "")
            alt = element.get("alt", "图片")
            if src:
                src = html.unescape(src)
                if src.startswith("//"):
                    src = "https:" + src
                # 对于今日头条图片，保留完整的 URL（包含查询参数）
                if "toutiao" not in src:
                    if "?" in src:
                        src = src.split("?")[0]
                return f"\n\n![{alt}]({src})\n\n"
            return ""
        
        elif tag_name == "br":
            return "\n"
        
        elif tag_name == "hr":
            return "\n\n---\n\n"
        
        elif tag_name in ["ul", "ol"]:
            items = []
            for i, li in enumerate(element.find_all("li", recursive=False)):
                item_content = MarkdownConverter._convert_element_to_markdown(li, platform).strip()
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
            return MarkdownConverter._convert_table_to_markdown(element)
        
        elif tag_name in ["div", "section", "article", "main"]:
            if children_text.strip():
                return f"\n{children_text}\n"
            return ""
        
        elif tag_name == "span":
            return children_text
        
        else:
            return children_text
    
    @staticmethod
    def _convert_table_to_markdown(table: Tag) -> str:
        """将 HTML 表格转换为 Markdown 表格"""
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
    
    @staticmethod
    def _clean_markdown(markdown: str) -> str:
        """清理 Markdown 内容"""
        if not markdown:
            return ""
        
        markdown = html.unescape(markdown)
        
        markdown = MarkdownConverter._fix_false_headings(markdown)
        
        markdown = MarkdownConverter._convert_chinese_section_to_heading(markdown)
        
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
    
    @staticmethod
    def _convert_chinese_section_to_heading(markdown: str) -> str:
        """将中文章节标题转换为 Markdown 标题"""
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
    
    @staticmethod
    def _fix_false_headings(markdown: str) -> str:
        """修复被错误识别为标题的内容"""
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
    
    @staticmethod
    def generate_document(
        title: str,
        content: str,
        source_url: str = "",
        author: str = "",
        publish_time: str = "",
        tags: list[str] = None,
    ) -> str:
        """
        生成完整的 Markdown 文档
        
        Args:
            title: 文章标题
            content: 正文内容
            source_url: 原文链接
            author: 作者名称
            publish_time: 发布时间
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

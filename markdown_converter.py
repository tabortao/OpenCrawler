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
    if not html or not html.strip():
        return ""
    
    soup = BeautifulSoup(html, "html.parser")
    
    if strip_scripts:
        for script in soup.find_all("script"):
            script.decompose()
    
    if strip_styles:
        for style in soup.find_all("style"):
            style.decompose()
    
    for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith("<!--")):
        comment.extract()
    
    if platform == "wechat":
        _process_wechat_images(soup)
        _process_wechat_br(soup)
    elif platform == "zhihu":
        _process_zhihu_content(soup)
    elif platform == "xiaohongshu":
        _process_xiaohongshu_content(soup)
    
    markdown = md(
        str(soup),
        heading_style="atx",
        bullets="-",
        strip=["script", "style", "nav", "header", "footer"],
        escape_asterisks=False,
        escape_underscores=False,
    )
    
    markdown = _clean_markdown(markdown)
    
    return markdown


def _process_wechat_images(soup: BeautifulSoup) -> None:
    for img in soup.find_all("img"):
        data_src = img.get("data-src")
        if data_src:
            img["src"] = data_src
            del img["data-src"]
        
        for attr in list(img.attrs.keys()):
            if attr not in ["src", "alt", "title"]:
                del img[attr]


def _process_wechat_br(soup: BeautifulSoup) -> None:
    for br in soup.find_all("br"):
        br.replace_with("\n")


def _process_zhihu_content(soup: BeautifulSoup) -> None:
    for nav in soup.find_all(["nav", "header"]):
        nav.decompose()
    
    for button in soup.find_all("button"):
        button.decompose()
    
    for a in soup.find_all("a"):
        if a.get("class") and any("Button" in c for c in a.get("class", [])):
            a.decompose()


def _process_xiaohongshu_content(soup: BeautifulSoup) -> None:
    for span in soup.find_all("span"):
        if span.get("class") and any("note-text" in c for c in span.get("class", [])):
            continue
        span.unwrap()


def _clean_markdown(markdown: str) -> str:
    if not markdown:
        return ""
    
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = re.sub(r"^\s+|\s+$", "", markdown, flags=re.MULTILINE)
    markdown = markdown.strip()
    
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


def extract_images_from_html(html: str) -> list[str]:
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

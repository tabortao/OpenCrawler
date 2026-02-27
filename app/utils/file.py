"""
文件工具模块

提供文件名处理、目录操作等功能
"""

import os
import re
from datetime import datetime
from typing import Optional


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
    
    Returns:
        清理后的文件名
    """
    if not filename:
        return ""
    
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    filename = re.sub(r"\s+", "_", filename)
    filename = filename.strip("._")
    
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename


def ensure_dir(dir_path: str) -> str:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        dir_path: 目录路径
    
    Returns:
        目录路径
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    return dir_path


def generate_article_filename(
    title: str,
    date: Optional[datetime] = None,
    extension: str = ".md",
) -> str:
    """
    生成文章文件名
    
    Args:
        title: 文章标题
        date: 日期，默认为当前日期
        extension: 文件扩展名
    
    Returns:
        文件名
    """
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime("%Y-%m-%d")
    safe_title = sanitize_filename(title) or "untitled"
    
    return f"{date_str}_{safe_title}{extension}"


def get_unique_filepath(
    directory: str,
    filename: str,
) -> str:
    """
    获取唯一的文件路径，如果文件已存在则添加序号
    
    Args:
        directory: 目录路径
        filename: 文件名
    
    Returns:
        唯一的文件路径
    """
    ensure_dir(directory)
    
    filepath = os.path.join(directory, filename)
    
    if not os.path.exists(filepath):
        return filepath
    
    name, ext = os.path.splitext(filename)
    counter = 1
    
    while os.path.exists(filepath):
        new_filename = f"{name}_{counter}{ext}"
        filepath = os.path.join(directory, new_filename)
        counter += 1
    
    return filepath


def get_file_hash(filepath: str) -> str:
    """
    计算文件的 MD5 哈希值
    
    Args:
        filepath: 文件路径
    
    Returns:
        MD5 哈希值
    """
    import hashlib
    
    hash_md5 = hashlib.md5()
    
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    
    return hash_md5.hexdigest()


def get_image_extension(url: str, content_type: str = "") -> str:
    """
    根据URL或内容类型获取图片扩展名
    
    Args:
        url: 图片 URL
        content_type: 内容类型
    
    Returns:
        图片扩展名
    """
    if content_type:
        if "webp" in content_type:
            return ".webp"
        elif "png" in content_type:
            return ".png"
        elif "gif" in content_type:
            return ".gif"
        elif "jpeg" in content_type or "jpg" in content_type:
            return ".jpg"
    
    from urllib.parse import urlparse
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    for ext in [".webp", ".png", ".gif", ".jpg", ".jpeg"]:
        if path.endswith(ext):
            return ext
    
    return ".jpg"

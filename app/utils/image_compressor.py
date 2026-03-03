"""
图片压缩器模块

提供图片压缩功能，支持 JPEG、PNG、WebP 格式
"""

import os
from typing import Optional, Tuple


class ImageCompressor:
    """
    图片压缩器
    
    支持 JPEG、PNG、WebP 格式的图片压缩
    """
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}
    
    def __init__(self, quality: int = 85):
        """
        初始化图片压缩器
        
        Args:
            quality: 压缩质量 (1-95)，默认 85
        """
        self.quality = max(1, min(95, quality))
        self._pillow_available = self._check_pillow()
    
    def _check_pillow(self) -> bool:
        """检查 Pillow 是否可用"""
        try:
            from PIL import Image
            return True
        except ImportError:
            return False
    
    def compress(self, input_path: str, output_path: Optional[str] = None) -> Tuple[bool, int, int]:
        """
        压缩图片
        
        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径，默认覆盖原文件
        
        Returns:
            (是否成功, 原始大小, 压缩后大小)
        """
        if not self._pillow_available:
            print("Pillow 未安装，跳过压缩")
            return False, 0, 0
        
        ext = os.path.splitext(input_path)[1].lower()
        if ext not in self.SUPPORTED_FORMATS:
            print(f"不支持的图片格式: {ext}")
            return False, 0, 0
        
        if output_path is None:
            output_path = input_path
        
        try:
            from PIL import Image
            
            original_size = os.path.getsize(input_path)
            
            with Image.open(input_path) as img:
                original_mode = img.mode
                
                if ext in {'.jpg', '.jpeg'}:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.save(output_path, "JPEG", optimize=True, quality=self.quality)
                elif ext == '.png':
                    img.save(output_path, "PNG", optimize=True)
                elif ext == '.webp':
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.save(output_path, "WEBP", optimize=True, quality=self.quality)
            
            compressed_size = os.path.getsize(output_path)
            saved_bytes = original_size - compressed_size
            saved_percent = (saved_bytes / original_size * 100) if original_size > 0 else 0
            
            print(f"压缩完成: {os.path.basename(input_path)} - "
                  f"原始: {self._format_size(original_size)} -> "
                  f"压缩后: {self._format_size(compressed_size)} "
                  f"(节省 {saved_percent:.1f}%)")
            
            return True, original_size, compressed_size
        
        except Exception as e:
            print(f"压缩失败: {input_path} - {e}")
            return False, 0, 0
    
    def compress_in_place(self, filepath: str) -> Tuple[bool, int, int]:
        """
        原地压缩图片（覆盖原文件）
        
        Args:
            filepath: 图片文件路径
        
        Returns:
            (是否成功, 原始大小, 压缩后大小)
        """
        return self.compress(filepath, filepath)
    
    def _format_size(self, size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 字节数
        
        Returns:
            可读的大小字符串
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"
    
    @staticmethod
    def is_supported(filepath: str) -> bool:
        """
        检查文件是否支持压缩
        
        Args:
            filepath: 文件路径
        
        Returns:
            是否支持
        """
        ext = os.path.splitext(filepath)[1].lower()
        return ext in ImageCompressor.SUPPORTED_FORMATS

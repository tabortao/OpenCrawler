"""
图片下载和压缩测试脚本
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crawlers.image_downloader import ImageDownloader
from app.utils.image_compressor import ImageCompressor


def test_image_compressor():
    """测试 ImageCompressor"""
    print("=" * 50)
    print("测试 ImageCompressor")
    print("=" * 50)

    # 检查 Pillow 是否可用
    try:
        from PIL import Image
        print("Pillow 已安装")
    except ImportError:
        print("Pillow 未安装")
        return

    # 测试压缩器
    compressor = ImageCompressor(quality=30)
    print(f"压缩器初始化完成, quality={compressor.quality}")

    # 查找一个测试图片
    test_dir = r"f:\Code\Python-Project\OpenCrawler\output\images\2026\03"
    if os.path.exists(test_dir):
        files = [f for f in os.listdir(test_dir) if f.endswith('.webp')]
        if files:
            test_file = os.path.join(test_dir, files[0])
            print(f"\n找到测试图片: {test_file}")

            original_size = os.path.getsize(test_file)
            print(f"原始大小: {original_size} bytes")

            # 执行压缩
            success, orig, compressed = compressor.compress(test_file)
            print(f"\n压缩结果: success={success}, original={orig}, compressed={compressed}")
            if success:
                print(f"节省: {orig - compressed} bytes ({(orig - compressed) / orig * 100:.1f}%)")


def test_image_downloader():
    """测试 ImageDownloader"""
    print("\n" + "=" * 50)
    print("测试 ImageDownloader")
    print("=" * 50)

    output_dir = r"f:\Code\Python-Project\OpenCrawler\output"
    test_url = "https://p3-sign.toutiaoimg.com/tos-cn-i-6w9myzkscx/f4d98e0332e049afaa067b81f35c59cb~tplv-tt-obj:webp.image"

    # 测试不压缩
    print("\n--- 测试不压缩 ---")
    with ImageDownloader(output_dir, compress=False) as downloader:
        print(f"ImageDownloader compress={downloader.compress}")
        result = downloader.download_image(test_url)
        print(f"下载结果: {result}")
        stats = downloader.get_compress_stats()
        print(f"统计: {stats}")

    # 测试压缩
    print("\n--- 测试压缩 ---")
    with ImageDownloader(output_dir, compress=True, compress_quality=30) as downloader:
        print(f"ImageDownloader compress={downloader.compress}, quality={downloader.compress_quality}")
        result = downloader.download_image(test_url)
        print(f"下载结果: {result}")
        stats = downloader.get_compress_stats()
        print(f"统计: {stats}")


if __name__ == "__main__":
    test_image_compressor()
    test_image_downloader()

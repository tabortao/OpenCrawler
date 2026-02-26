"""
多平台 Markdown 转换测试脚本

测试知乎、微信公众号、小红书的 Markdown 转换效果。
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler import extract_url, save_article
from utils import detect_platform


# 测试 URL 配置
TEST_URLS = {
    "xiaohongshu": "http://xhslink.com/o/5Msx6KHENIf",
    "zhihu": "https://zhuanlan.zhihu.com/p/1955562956793288631",
    "wechat": "https://mp.weixin.qq.com/s/g1KA0ndaKCGlEhlD9p6ofA",
}


def print_separator(title: str):
    """打印分隔线"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


def print_markdown_preview(markdown: str, max_lines: int = 30):
    """打印 Markdown 预览"""
    if not markdown:
        print("  (内容为空)")
        return
    
    lines = markdown.split('\n')
    for i, line in enumerate(lines[:max_lines]):
        print(f"  {line}")
    
    if len(lines) > max_lines:
        print(f"  ... (共 {len(lines)} 行)")


async def test_platform(platform: str, url: str, download_images: bool = False):
    """
    测试单个平台的转换效果
    
    Args:
        platform: 平台名称
        url: 测试 URL
        download_images: 是否下载图片
    """
    print_separator(f"测试平台: {platform}")
    print(f"URL: {url}")
    
    try:
        # 提取内容
        print("\n正在提取内容...")
        result = await extract_url(url)
        
        print(f"\n标题: {result.get('title', 'N/A')}")
        print(f"Markdown 长度: {len(result.get('markdown', ''))}")
        print(f"图片数量: {len(result.get('image_urls', []))}")
        
        # 保存文件
        print("\n正在保存文件...")
        filepath = save_article(
            title=result["title"],
            url=result["url"],
            markdown=result["markdown"],
            html=result.get("html", ""),
            image_urls=result.get("image_urls", []),
            download_images=download_images,
            platform=platform,
        )
        print(f"保存路径: {filepath}")
        
        # 打印 Markdown 预览
        print("\nMarkdown 预览:")
        print_markdown_preview(result.get("markdown", ""))
        
        return True, filepath
        
    except ValueError as e:
        error_msg = str(e)
        if "Cookie" in error_msg:
            print(f"\n❌ Cookie 过期: {error_msg}")
        else:
            print(f"\n❌ 错误: {error_msg}")
        return False, None
        
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def run_all_tests(platforms: list = None, download_images: bool = False):
    """
    运行所有测试
    
    Args:
        platforms: 要测试的平台列表，None 表示测试所有平台
        download_images: 是否下载图片
    """
    print_separator("多平台 Markdown 转换测试")
    print(f"下载图片: {'是' if download_images else '否'}")
    
    if platforms is None:
        platforms = list(TEST_URLS.keys())
    
    results = {}
    
    for platform in platforms:
        if platform not in TEST_URLS:
            print(f"\n⚠️  未知平台: {platform}")
            continue
        
        url = TEST_URLS[platform]
        success, filepath = await test_platform(platform, url, download_images)
        results[platform] = {
            "success": success,
            "filepath": filepath,
        }
    
    # 打印汇总
    print_separator("测试结果汇总")
    
    success_count = 0
    for platform, result in results.items():
        status = "✅ 成功" if result["success"] else "❌ 失败"
        filepath = result["filepath"] or "N/A"
        print(f"  {platform}: {status}")
        if result["filepath"]:
            print(f"    文件: {filepath}")
        if result["success"]:
            success_count += 1
    
    print(f"\n总计: {success_count}/{len(results)} 成功")
    
    return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="多平台 Markdown 转换测试")
    parser.add_argument(
        "--platform", "-p",
        choices=["xiaohongshu", "zhihu", "wechat", "all"],
        default="all",
        help="要测试的平台 (默认: all)"
    )
    parser.add_argument(
        "--download-images", "-d",
        action="store_true",
        help="下载图片到本地"
    )
    
    args = parser.parse_args()
    
    if args.platform == "all":
        platforms = None
    else:
        platforms = [args.platform]
    
    asyncio.run(run_all_tests(platforms=platforms, download_images=args.download_images))


if __name__ == "__main__":
    main()

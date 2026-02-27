"""
测试图片下载器

验证图片下载器是否能正确下载今日头条的图片
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crawlers.image_downloader import ImageDownloader


def test_toutiao_image_download():
    """测试下载今日头条图片"""
    # 测试图片 URL
    test_image_url = "https://p3-sign.toutiaoimg.com/tos-cn-i-axegupay5k/a233a88b213d4d1f97edd1f4ea9ebce0~tplv-tt-origin-web:gif.jpeg"
    
    # 创建图片下载器
    output_dir = "output"
    downloader = ImageDownloader(output_dir)
    
    try:
        print(f"测试下载图片: {test_image_url}")
        
        # 手动测试下载过程
        import httpx
        
        # 构建请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.toutiao.com/",
        }
        
        print("发送请求...")
        response = httpx.get(test_image_url, headers=headers, timeout=30, follow_redirects=True)
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_length = len(response.content)
            print(f"内容类型: {content_type}")
            print(f"内容长度: {content_length} 字节")
            
            # 保存测试文件
            test_file = os.path.join(output_dir, "test_image.jpg")
            with open(test_file, "wb") as f:
                f.write(response.content)
            print(f"✓ 测试文件保存成功: {test_file}")
        else:
            print(f"✗ 下载失败，状态码: {response.status_code}")
        
        # 测试下载器
        print("\n使用下载器测试...")
        local_path = downloader.download_image(test_image_url)
        
        if local_path:
            print(f"✓ 下载成功: {local_path}")
            
            # 检查文件是否存在
            full_path = os.path.join(output_dir, local_path)
            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                print(f"✓ 文件存在，大小: {file_size} 字节")
            else:
                print(f"✗ 文件不存在: {full_path}")
        else:
            print(f"✗ 下载失败")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        downloader.close()


if __name__ == "__main__":
    test_toutiao_image_download()
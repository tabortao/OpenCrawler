"""
测试今日头条图片下载

使用用户提供的完整图片链接测试下载功能
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crawlers.image_downloader import ImageDownloader


def test_toutiao_image_download():
    """测试下载今日头条图片"""
    # 用户提供的完整图片 URL
    test_image_url = "https://p3-sign.toutiaoimg.com/tos-cn-i-axegupay5k/a233a88b213d4d1f97edd1f4ea9ebce0~tplv-tt-origin-web:gif.jpeg?_iz=58558&from=article.pc_detail&lk3s=953192f4&x-expires=1772767581&x-signature=2psMubKKoWyXk%2FX6i%2BmsC0t%2BgdI%3D"
    
    # 创建图片下载器
    output_dir = "output"
    downloader = ImageDownloader(output_dir)
    
    try:
        print(f"测试下载图片: {test_image_url}")
        
        # 下载图片
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
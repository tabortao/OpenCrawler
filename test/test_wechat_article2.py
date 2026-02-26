"""
测试微信公众号文章下载 - 带微信样式标题的文章

测试 URL: https://mp.weixin.qq.com/s/kosxCq8j9y3J8pF_CRvecg
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler import extract_url, save_article


async def test_wechat_article():
    url = "https://mp.weixin.qq.com/s/kosxCq8j9y3J8pF_CRvecg"
    
    print(f"开始测试微信公众号文章下载...")
    print(f"URL: {url}")
    print("-" * 50)
    
    try:
        result = await extract_url(url)
        
        if result.get("status") == "success":
            print(f"✅ 标题: {result['title']}")
            print(f"✅ Markdown 长度: {len(result['markdown'])} 字符")
            print(f"✅ 图片数量: {len(result.get('image_urls', []))}")
            
            filepath = save_article(
                title=result["title"],
                url=result["url"],
                markdown=result["markdown"],
                html=result.get("html", ""),
                image_urls=result.get("image_urls", []),
                download_images=True,
                platform="wechat",
            )
            
            print(f"✅ 文件已保存: {filepath}")
            
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            print("\n" + "=" * 50)
            print("文件内容预览 (前 3000 字符):")
            print("=" * 50)
            print(content[:3000])
            
            if len(content) > 3000:
                print(f"\n... (还有 {len(content) - 3000} 字符)")
            
            return filepath
        else:
            print(f"❌ 提取失败: {result}")
            return None
            
    except Exception as e:
        import traceback
        print(f"❌ 测试失败: {e}")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_wechat_article())

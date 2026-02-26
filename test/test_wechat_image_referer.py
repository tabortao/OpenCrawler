"""
测试微信图片下载防盗链
"""
import httpx


def test_wechat_image_download():
    """测试微信图片下载防盗链"""
    test_urls = [
        "https://mmbiz.qpic.cn/mmbiz_png/KOurXFyxfQqQx7aZRzHIA3QnUFARy0qGLPw96mNcr1zVB37faWL2DYYzbPZ9SQt9yfZibJ0tYibiaLZgJQZtQF7w/640?wx_fmt=png&from=appmsg",
    ]
    
    # 测试不同的请求头组合
    headers_list = [
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://mp.weixin.qq.com/",
        },
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://mp.weixin.qq.com/",
        },
    ]
    
    client = httpx.Client(timeout=30, follow_redirects=True)
    
    for url in test_urls:
        print(f"\n测试 URL: {url[:60]}...")
        
        for i, headers in enumerate(headers_list):
            try:
                response = client.get(url, headers=headers)
                print(f"  请求头组合 {i+1}: 状态码 {response.status_code}, 内容长度 {len(response.content)}")
                if response.status_code == 200 and len(response.content) > 1000:
                    # 检查是否是防盗链图片
                    content_type = response.headers.get("content-type", "")
                    print(f"    Content-Type: {content_type}")
                    # 保存图片检查
                    with open(f"test_image_{i+1}.jpg", "wb") as f:
                        f.write(response.content)
                    print(f"    已保存为 test_image_{i+1}.jpg")
            except Exception as e:
                print(f"  请求头组合 {i+1}: 失败 - {e}")
    
    client.close()


if __name__ == "__main__":
    test_wechat_image_download()

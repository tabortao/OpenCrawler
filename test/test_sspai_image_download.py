"""
测试少数派图片下载
"""
import httpx


def test_sspai_image_download():
    """测试少数派图片下载"""
    test_urls = [
        "https://cdnfile.sspai.com/2026/02/22/article/2bebfbd4b87649906b53c7f00238b0f5.png",
        "https://cdn-static.sspai.com/ui/tags/matrix.png",
        "https://cdnfile.sspai.com/2026/02/22/c7ecb6bb80d87c6fe1142b6be2cc1c00.jpg",
    ]
    
    # 测试不同的请求头组合
    headers_list = [
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://sspai.com/",
        },
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://sspai.com/",
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
                    print(f"    ✓ 成功!")
                    break
            except Exception as e:
                print(f"  请求头组合 {i+1}: 失败 - {e}")
    
    client.close()


if __name__ == "__main__":
    test_sspai_image_download()

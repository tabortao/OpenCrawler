"""
测试微信文章 API
"""
import httpx
import asyncio


async def test_wechat_article():
    """测试微信文章下载"""
    url = "http://127.0.0.1:8000/api/v1/articles"
    
    payload = {
        "url": "https://mp.weixin.qq.com/s/FFGnheRRKS70QpHpPTXyyQ",
        "download_images": True
    }
    
    async with httpx.AsyncClient(timeout=120) as client:
        print(f"正在请求: {url}")
        print(f"参数: {payload}")
        
        response = await client.post(url, json=payload)
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")


if __name__ == "__main__":
    asyncio.run(test_wechat_article())

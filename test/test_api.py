import httpx

BASE_URL = "http://127.0.0.1:8000"


def test_health_check():
    response = httpx.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Web Markdown Extractor"
    print("✅ 健康检查通过")


def test_extract_invalid_url():
    response = httpx.get(
        f"{BASE_URL}/extract",
        params={"url": "invalid-url"},
        timeout=10
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert data["error"] == "INVALID_URL"
    print("✅ 无效 URL 测试通过")


def test_extract_missing_url():
    response = httpx.get(f"{BASE_URL}/extract", timeout=10)
    assert response.status_code == 422
    print("✅ 缺少 URL 参数测试通过")


def test_extract_github():
    response = httpx.get(
        f"{BASE_URL}/extract",
        params={"url": "https://github.com/fastapi/fastapi"},
        timeout=60
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["url"] == "https://github.com/fastapi/fastapi"
    assert len(data["markdown"]) > 100
    assert "FastAPI" in data["markdown"] or "fastapi" in data["markdown"].lower()
    print(f"✅ GitHub 提取测试通过 - 标题: {data['title']}")
    print(f"   内容长度: {len(data['markdown'])} 字符")


def test_extract_python_org():
    response = httpx.get(
        f"{BASE_URL}/extract",
        params={"url": "https://www.python.org/"},
        timeout=60
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["markdown"]) > 50
    print(f"✅ Python.org 提取测试通过 - 标题: {data['title']}")


def run_all_tests():
    print("\n" + "=" * 50)
    print("开始运行 API 测试")
    print("=" * 50 + "\n")

    try:
        test_health_check()
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return

    try:
        test_extract_invalid_url()
    except Exception as e:
        print(f"❌ 无效 URL 测试失败: {e}")

    try:
        test_extract_missing_url()
    except Exception as e:
        print(f"❌ 缺少 URL 参数测试失败: {e}")

    try:
        test_extract_github()
    except Exception as e:
        print(f"❌ GitHub 提取测试失败: {e}")

    try:
        test_extract_python_org()
    except Exception as e:
        print(f"❌ Python.org 提取测试失败: {e}")

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()

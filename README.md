# 多平台网页 Markdown 提取 API

基于 FastAPI + Playwright 的高性能网页内容提取服务，支持将网页正文转换为干净的 Markdown 格式。

## 功能特性

- **多平台支持**: GitHub、知乎、小红书、微信公众号等
- **动态渲染**: 支持 JavaScript 渲染，处理动态加载内容
- **反爬避让**: 浏览器指纹伪装，绕过反爬机制
- **Cookie 注入**: 支持知乎、小红书等需要登录的平台
- **代理支持**: 支持通过代理服务器请求
- **图片下载**: 可选下载图片到本地，Markdown 中引用本地路径
- **内容优化**: 知乎标题过滤私信消息、内容过滤导航元素

## 快速开始

### 环境要求

- Python 3.10+
- micromamba (推荐) 或 conda

### 安装步骤

```bash
# 1. 创建虚拟环境
micromamba create -p ./venv python=3.11 -y

# 2. 安装依赖
micromamba run -p ./venv python -m pip install -r requirements.txt

# 3. 安装 Playwright 浏览器
micromamba run -p ./venv playwright install chromium

# 4. 配置环境变量 (可选)
cp .env.example .env
```

### 启动服务

```bash
micromamba run -p ./venv python main.py
# 服务将在 http://127.0.0.1:8000 启动
```

## API 使用说明

### 健康检查

```bash
GET /api/v1/health
```

**响应示例:**
```json
{
  "status": "healthy",
  "service": "Web Markdown Extractor",
  "version": "2.0.0"
}
```

### 获取网页标题

```bash
GET /api/v1/pages/title?url=<网页URL>
```

**参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | 要获取标题的网页 URL |

**成功响应 (200):**
```json
{
  "url": "https://example.com",
  "title": "网页标题"
}
```

**标题不存在响应 (404):**
```json
{
  "error": "TITLE_NOT_FOUND",
  "message": "该网页没有标题"
}
```

### 提取网页内容

```bash
POST /api/v1/pages/extract
Content-Type: application/json

{
  "url": "https://example.com"
}
```

**请求参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | 要提取内容的网页 URL |

**成功响应 (200):**
```json
{
  "title": "文章标题",
  "url": "https://example.com",
  "markdown": "正文内容...",
  "html": "<p>原始HTML</p>",
  "image_urls": ["https://example.com/img1.jpg"]
}
```

### 创建文章（保存为文件）

```bash
POST /api/v1/articles
Content-Type: application/json

{
  "url": "https://example.com",
  "download_images": true
}
```

**请求参数:**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| url | string | 是 | - | 要提取并保存的网页 URL |
| download_images | boolean | 否 | false | 是否下载图片到本地 |

**成功响应 (200):**
```json
{
  "title": "文章标题",
  "url": "https://example.com",
  "filepath": "output/2026-02-24_文章标题.md"
}
```

**错误响应:**
```json
{
  "error": "ERROR_CODE",
  "message": "错误详情描述"
}
```

### 使用示例

```bash
# 健康检查
curl http://127.0.0.1:8000/api/v1/health

# 获取网页标题
curl "http://127.0.0.1:8000/api/v1/pages/title?url=https://zhuanlan.zhihu.com/p/1955562956793288631"

# 提取 GitHub README
curl -X POST http://127.0.0.1:8000/api/v1/pages/extract -H "Content-Type: application/json" -d '{"url": "https://github.com/fastapi/fastapi"}'

# 保存微信文章（不下载图片）
curl -X POST http://127.0.0.1:8000/api/v1/articles -H "Content-Type: application/json" -d '{"url": "https://mp.weixin.qq.com/s/g1KA0ndaKCGlEhlD9p6ofA"}'

# 保存知乎文章并下载图片
curl -X POST http://127.0.0.1:8000/api/v1/articles -H "Content-Type: application/json" -d '{"url": "https://zhuanlan.zhihu.com/p/1955562956793288631", "download_images": true}'
```

### HTTP 状态码说明

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | OK | 请求成功 |
| 400 | Bad Request | URL 格式错误 |
| 401 | Unauthorized | Cookie 已过期，需要更新 |
| 404 | Not Found | 资源不存在（如标题不存在） |
| 422 | Unprocessable Entity | 页面内容为空或无法解析 |
| 500 | Internal Server Error | 服务器内部错误 |
| 504 | Gateway Timeout | 请求超时 |

## 平台配置

| 平台 | 选择器 | 特殊处理 |
|------|--------|----------|
| GitHub | `.markdown-body` | 无 |
| 知乎 | `.Post-RichText` | Cookie 注入、标题过滤私信、内容过滤导航 |
| 小红书 | `.note-content` | Cookie + 代理 |
| 微信公众号 | `.rich_media_content` | data-src 图片提取 |

## 环境变量配置

```env
# 服务器配置
HOST=127.0.0.1
PORT=8000

# 输出目录
OUTPUT_DIR=output

# 反爬配置
PROXY_URL=http://user:pass@host:port

# 平台 Cookie
ZHIHU_COOKIE=name=value; name2=value2
XHS_COOKIE=name=value; name2=value2
```

## 输出格式

保存的文章包含 YAML front matter 和格式化的内容：

```markdown
---
title: 文章标题
url: https://example.com/article
date: 2026-02-24 12:00:00
tags: [web-crawler]
---

# 文章标题

> 来源: [https://example.com/article](https://example.com/article)

---

正文内容...

![图片1](images/abc123.webp)

```python
def hello():
    print("Hello, World!")
```
```

## 项目结构

```
MyCrawler/
├── main.py              # FastAPI 入口与路由
├── crawler.py           # Playwright 爬虫核心逻辑
├── utils.py             # 工具函数
├── requirements.txt     # 依赖列表
├── .env.example         # 环境变量模版
├── output/              # 文章输出目录
│   ├── *.md             # Markdown 文件
│   └── images/          # 图片目录
└── docs/
    └── 需求文档.md
```

## API 文档

启动服务后访问：
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 注意事项

### uvicorn reload 模式问题

**重要**: `main.py` 中的 `reload=False` 不能改为 `True`！

当使用 `uvicorn.run("main:app", reload=True)` 启动时，uvicorn 会创建一个 reloader 进程来监控文件变化，这会导致：

1. **模块被多次加载** - 可以看到日志中模块加载信息出现两次
2. **异步任务执行异常** - 爬取请求没有被正确处理，服务端日志完全没有显示爬取过程
3. **结果为空** - 生成的 Markdown 文件只有标题，没有内容和图片

**解决方案**: 生产环境必须使用 `reload=False`。如果需要开发调试：
- 使用测试脚本 `test_xhs_direct.py` 直接测试爬虫功能
- 或者单独启动服务进行测试，但不要依赖 reload 功能

## 许可证

MIT License

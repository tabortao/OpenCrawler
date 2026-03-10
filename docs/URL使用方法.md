# OpenCrawler API 接口文档

本文档详细介绍 OpenCrawler 项目所有 API 接口的使用方法。

---

## 目录

- [概述](#概述)
- [认证方式](#认证方式)
- [通用响应格式](#通用响应格式)
- [系统 API](#系统-api)
- [页面 API](#页面-api)
- [文章 API](#文章-api)
- [错误码说明](#错误码说明)
- [常见问题](#常见问题)

---

## 概述

### 基础信息

| 项目 | 说明 |
|------|------|
| 基础 URL | `http://127.0.0.1:8000` |
| API 前缀 | `/api/v1` |
| 协议 | HTTP/HTTPS |
| 数据格式 | JSON |
| 编码 | UTF-8 |

### 支持的平台

| 平台 | 标识符 | 说明 |
|------|--------|------|
| GitHub | `github` | 仓库 README、文档 |
| 知乎 | `zhihu` | 专栏文章（需要 Cookie） |
| 小红书 | `xiaohongshu` | 笔记内容（需要 Cookie） |
| 微信公众号 | `wechat` | 公众号文章 |
| 少数派 | `sspai` | 文章内容 |
| 今日头条 | `toutiao` | 新闻文章 |
| 通用网页 | `generic` | 自动识别内容 |

---

## 认证方式

如果配置了 `API_TOKEN` 环境变量，所有 API 请求（健康检查除外）都需要携带认证令牌。

### 生成令牌

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 认证方式

支持两种认证方式：

#### 方式1：Bearer Token（推荐）

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://127.0.0.1:8000/api/v1/articles
```

#### 方式2：X-API-Token

```bash
curl -H "X-API-Token: YOUR_TOKEN" http://127.0.0.1:8000/api/v1/articles
```

### 认证错误响应

| 状态码 | 说明 |
|--------|------|
| 401 | 缺少认证令牌或令牌无效 |

```json
{
  "detail": "缺少认证令牌，请在请求头中提供 Authorization: Bearer <token> 或 X-API-Token: <token>"
}
```

---

## 通用响应格式

### 成功响应

```json
{
  "title": "文章标题",
  "url": "https://example.com/article",
  "markdown": "Markdown 内容...",
  "html": "<p>HTML 内容...</p>",
  "image_urls": ["https://example.com/image1.jpg"]
}
```

### 错误响应

```json
{
  "error": "ERROR_CODE",
  "message": "错误详情描述",
  "url": "请求的 URL"
}
```

---

## 系统 API

### 健康检查

检查服务是否正常运行。

| 项目 | 说明 |
|------|------|
| URL | `/api/v1/health` |
| 方法 | `GET` |
| 认证 | 不需要 |

#### 请求示例

```bash
curl http://127.0.0.1:8000/api/v1/health
```

#### 成功响应

```json
{
  "status": "healthy"
}
```

---

## 页面 API

### 获取网页标题

获取指定 URL 的网页标题。

| 项目 | 说明 |
|------|------|
| URL | `/api/v1/pages/title` |
| 方法 | `GET` |
| 认证 | 需要（如果配置了 API_TOKEN） |

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `url` | string | 是 | - | 要获取标题的网页 URL |

#### 请求头

| 头名称 | 必填 | 说明 |
|--------|------|------|
| `Authorization` | 可选 | Bearer Token 认证 |
| `X-API-Token` | 可选 | API Token 认证 |

#### 请求示例

```bash
# 无认证
curl "http://127.0.0.1:8000/api/v1/pages/title?url=https://sspai.com/post/105218"

# 有认证
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/api/v1/pages/title?url=https://sspai.com/post/105218"
```

#### 成功响应

**状态码：** `200 OK`

```json
{
  "url": "https://sspai.com/post/105218",
  "title": "文章标题"
}
```

#### 错误响应

| 状态码 | 错误码 | 说明 |
|--------|--------|------|
| 400 | `INVALID_URL` | URL 格式不正确 |
| 404 | `TITLE_NOT_FOUND` | 该网页没有标题 |
| 408 | `TIMEOUT` | 请求超时 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 |

---

### 提取页面内容

从指定 URL 提取网页内容并转换为 Markdown 格式。

| 项目 | 说明 |
|------|------|
| URL | `/api/v1/pages/extract` |
| 方法 | `POST` |
| 认证 | 需要（如果配置了 API_TOKEN） |

#### 请求头

| 头名称 | 必填 | 说明 |
|--------|------|------|
| `Content-Type` | 是 | `application/json` |
| `Authorization` | 可选 | Bearer Token 认证 |
| `X-API-Token` | 可选 | API Token 认证 |

#### 请求体

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `url` | string | 是 | - | 要提取内容的网页 URL |

#### 请求示例

```bash
curl -X POST http://127.0.0.1:8000/api/v1/pages/extract \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"url": "https://sspai.com/post/105218"}'
```

#### 成功响应

**状态码：** `200 OK`

```json
{
  "title": "文章标题",
  "url": "https://sspai.com/post/105218",
  "markdown": "# 文章标题\n\n文章内容...",
  "html": "<h1>文章标题</h1><p>文章内容...</p>",
  "image_urls": [
    "https://cdn.sspai.com/image1.jpg",
    "https://cdn.sspai.com/image2.jpg"
  ]
}
```

#### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | 文章标题 |
| `url` | string | 原始 URL |
| `markdown` | string | Markdown 格式内容 |
| `html` | string | HTML 格式内容 |
| `image_urls` | array | 图片 URL 列表 |

---

## 文章 API

### 创建文章

从指定 URL 提取内容并保存为 Markdown 文件。

| 项目 | 说明 |
|------|------|
| URL | `/api/v1/articles` |
| 方法 | `POST` |
| 认证 | 需要（如果配置了 API_TOKEN） |

#### 请求头

| 头名称 | 必填 | 说明 |
|--------|------|------|
| `Content-Type` | 是 | `application/json` |
| `Authorization` | 可选 | Bearer Token 认证 |
| `X-API-Token` | 可选 | API Token 认证 |

#### 请求体

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `url` | string | 是 | - | 要提取的网页 URL |
| `download_images` | boolean | 否 | `false` | 是否下载图片到本地 |
| `compress_images` | boolean | 否 | `false` | 是否压缩图片（需启用 download_images） |
| `compress_quality` | integer | 否 | `85` | 压缩质量 (1-95) |

#### 请求示例

**基本请求（不下载图片）：**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/articles \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"url": "https://zhuanlan.zhihu.com/p/123456789"}'
```

**下载图片：**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/articles \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"url": "https://mp.weixin.qq.com/s/xxx", "download_images": true}'
```

**下载并压缩图片：**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/articles \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "url": "https://sspai.com/post/105218",
    "download_images": true,
    "compress_images": true,
    "compress_quality": 70
  }'
```

#### 成功响应

**状态码：** `200 OK`

```json
{
  "title": "文章标题",
  "url": "https://sspai.com/post/105218",
  "filepath": "output/2026-03-04_文章标题.md",
  "compress_stats": {
    "total_images": 10,
    "compressed_images": 8,
    "total_original_size": 5242880,
    "total_compressed_size": 1572864,
    "compression_ratio": 0.70
  }
}
```

#### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | 文章标题 |
| `url` | string | 原始 URL |
| `filepath` | string | 保存的文件路径 |
| `compress_stats` | object | 图片压缩统计（仅启用压缩时返回） |

#### compress_stats 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_images` | integer | 图片总数 |
| `compressed_images` | integer | 已压缩图片数 |
| `total_original_size` | integer | 原始总大小（字节） |
| `total_compressed_size` | integer | 压缩后总大小（字节） |
| `compression_ratio` | float | 压缩比例 |

---

## 错误码说明

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败 |
| 404 | 资源不存在 |
| 408 | 请求超时 |
| 500 | 服务器内部错误 |

### 业务错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `INVALID_URL` | URL 格式不正确 | 检查 URL 是否包含协议（http/https） |
| `TITLE_NOT_FOUND` | 网页没有标题 | 正常情况，返回空标题 |
| `TIMEOUT` | 请求超时 | 检查目标网站是否可访问，稍后重试 |
| `AUTHENTICATION_REQUIRED` | 需要登录 | 配置对应平台的 Cookie |
| `INTERNAL_ERROR` | 服务器内部错误 | 查看服务器日志，联系管理员 |

### 错误响应示例

**URL 格式错误：**

```json
{
  "error": "INVALID_URL",
  "message": "URL 格式不正确，请提供有效的 HTTP/HTTPS URL",
  "url": "invalid-url"
}
```

**请求超时：**

```json
{
  "error": "TIMEOUT",
  "message": "抓取超时，请稍后重试或检查目标网站是否可访问",
  "url": "https://example.com/slow-page"
}
```

**需要认证：**

```json
{
  "error": "AUTHENTICATION_REQUIRED",
  "message": "该平台需要登录，请在配置文件中设置 Cookie",
  "url": "https://zhuanlan.zhihu.com/p/xxx"
}
```

---

## 常见问题

### 1. 如何获取知乎 Cookie？

1. 打开 https://www.zhihu.com 并登录
2. 按 F12 打开开发者工具
3. 切换到 Application → Cookies
4. 复制所有 Cookie（格式：`name1=value1; name2=value2`）
5. 在 `.env` 文件中配置：`ZHIHU_COOKIE=复制的Cookie`

### 2. 如何获取小红书 Cookie？

1. 打开 https://www.xiaohongshu.com 并登录
2. 按 F12 打开开发者工具
3. 切换到 Application → Cookies
4. 复制所有 Cookie
5. 在 `.env` 文件中配置：`XHS_COOKIE=复制的Cookie`

### 3. 图片下载失败怎么办？

可能原因：
- 图片 URL 已失效
- 网络连接问题
- 图片服务器限制访问

解决方案：
- 检查网络连接
- 尝试不下载图片，直接获取 Markdown
- 检查目标网站是否有防盗链

### 4. 请求超时怎么办？

可能原因：
- 目标网站响应慢
- 网络连接不稳定
- 内容较多需要更长时间

解决方案：
- 稍后重试
- 检查目标网站是否可正常访问
- 考虑使用代理

### 5. 如何使用代理？

在 `.env` 文件中配置：

```env
PROXY_URL=http://127.0.0.1:7890
```

---

## 附录

### cURL 常用参数

| 参数 | 说明 |
|------|------|
| `-X POST` | 使用 POST 方法 |
| `-H "Header: Value"` | 添加请求头 |
| `-d '{"key": "value"}'` | 添加请求体 |
| `-o output.json` | 保存响应到文件 |
| `-v` | 显示详细信息 |

### 完整请求示例

```bash
# 提取微信公众号文章并下载压缩图片
curl -X POST http://127.0.0.1:8000/api/v1/articles \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "url": "https://mp.weixin.qq.com/s/abc123",
    "download_images": true,
    "compress_images": true,
    "compress_quality": 75
  }' \
  -o result.json
```

# 多平台网页 Markdown 提取 API

基于 FastAPI + Playwright 的高性能网页内容提取服务，支持将网页正文转换为干净的 Markdown 格式。

## 功能特性

- **多平台支持**: GitHub、知乎、小红书、微信公众号等
- **动态渲染**: 支持 JavaScript 渲染，处理动态加载内容
- **反爬避让**: 浏览器指纹伪装，绕过反爬机制
- **Cookie 注入**: 支持知乎、小红书等需要登录的平台
- **代理支持**: 支持通过代理服务器请求
- **图片保留**: 转换时保留图片链接
- **文章保存**: 支持将文章保存为 Markdown 文件

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
# 编辑 .env 文件配置代理和 Cookie
```

### 启动服务

```bash
# 启动开发服务器 (带热重载)
micromamba run -p ./venv python main.py

# 服务将在 http://127.0.0.1:8000 启动
```

## API 使用说明

### 健康检查

```bash
GET /health
```

**响应示例:**
```json
{
  "status": "healthy",
  "service": "Web Markdown Extractor"
}
```

### 提取网页内容

```bash
GET /extract?url=<网页URL>
```

**参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | 要提取内容的网页 URL |

**成功响应 (200):**
```json
{
  "status": "success",
  "title": "文章标题",
  "url": "原始URL",
  "markdown": "# 转换后的内容..."
}
```

**错误响应:**
| 状态码 | 错误类型 | 说明 |
|--------|----------|------|
| 400 | INVALID_URL | URL 格式不正确 |
| 422 | EMPTY_CONTENT | 页面内容为空或无法解析 |
| 500 | TIMEOUT/CRAWL_ERROR | 抓取超时或代理失效 |

### 保存文章到文件

```bash
GET /save?url=<网页URL>
```

**功能**: 提取网页内容并保存为 Markdown 文件到 `output` 目录

**文件命名格式**: `日期_标题.md` (如: `2026-02-15_FastAPI教程.md`)

**成功响应 (200):**
```json
{
  "status": "success",
  "title": "文章标题",
  "url": "原始URL",
  "filepath": "output/2026-02-15_文章标题.md"
}
```

### 使用示例

#### cURL

```bash
# 提取 GitHub README
curl "http://127.0.0.1:8000/extract?url=https://github.com/fastapi/fastapi"

# 提取并保存知乎文章
curl "http://127.0.0.1:8000/save?url=https://zhuanlan.zhihu.com/p/123456789"
```

#### Python

```python
import httpx

# 提取网页内容
response = httpx.get(
    "http://127.0.0.1:8000/extract",
    params={"url": "https://github.com/fastapi/fastapi"},
    timeout=60
)

if response.status_code == 200:
    data = response.json()
    print(f"标题: {data['title']}")
    print(f"内容:\n{data['markdown']}")
else:
    print(f"错误: {response.json()}")

# 保存文章到文件
response = httpx.get(
    "http://127.0.0.1:8000/save",
    params={"url": "https://zhuanlan.zhihu.com/p/123456789"},
    timeout=60
)
print(f"文件已保存到: {response.json()['filepath']}")
```

#### JavaScript (fetch)

```javascript
// 提取网页内容
const url = encodeURIComponent('https://github.com/fastapi/fastapi');
fetch(`http://127.0.0.1:8000/extract?url=${url}`)
  .then(res => res.json())
  .then(data => {
    console.log('标题:', data.title);
    console.log('内容:', data.markdown);
  })
  .catch(err => console.error('错误:', err));
```

## 平台配置

| 平台 | 选择器 | 超时时间 | 特殊处理 |
|------|--------|----------|----------|
| GitHub | `.markdown-body` | 15s | 无 |
| 知乎 | `.Post-RichText` | 20s | Cookie 注入 |
| 小红书 | `.note-content` | 20s | Cookie + 代理 |
| 微信公众号 | `.rich_media_content` | 15s | 过滤广告 |

## 环境变量配置

创建 `.env` 文件进行配置：

```env
# 服务器配置
HOST=127.0.0.1
PORT=8000

# 输出目录
OUTPUT_DIR=output

# 反爬配置
PROXY_URL=http://user:pass@host:port

# 平台 Cookie (知乎、小红书需要)
ZHIHU_COOKIE=name=value; name2=value2
XHS_COOKIE=name=value; name2=value2
```

## Cookie 获取教程

知乎和小红书等平台需要登录才能查看完整内容，因此需要配置 Cookie。

### 方法一：浏览器开发者工具 (推荐)

#### Chrome / Edge 步骤：

1. **打开目标网站并登录**
   - 访问 https://www.zhihu.com 并登录账号
   - 或访问 https://www.xiaohongshu.com 并登录账号

2. **打开开发者工具**
   - 按 `F12` 或右键页面选择"检查"

3. **切换到 Network 标签**
   - 点击顶部的 `Network` (网络) 标签
   - 如果没有请求，刷新页面 (F5)

4. **找到任意请求**
   - 点击列表中的任意请求
   - 在右侧面板中找到 `Headers` (标头)

5. **复制 Cookie**
   - 向下滚动找到 `Request Headers` 部分
   - 找到 `Cookie:` 行
   - 复制整个 Cookie 值 (可能很长)

6. **配置到 .env 文件**
   ```env
   ZHIHU_COOKIE=_zap=xxx; d_c0=xxx; q_c1=xxx; ...
   # 或
   XHS_COOKIE=a1=xxx; webId=xxx; ...
   ```

### 方法二：使用 EditThisCookie 扩展

1. 安装 Chrome 扩展 [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/)
2. 访问目标网站并登录
3. 点击扩展图标
4. 点击 "Export" 导出 Cookie
5. 将导出的内容粘贴到 `.env` 文件

### Cookie 格式说明

Cookie 格式为 `name1=value1; name2=value2; name3=value3`

示例：
```
ZHIHU_COOKIE=_zap=abc123; d_c0=AQAwBw; q_c1=xyz789; Hm_lvt_98beee=123456
```

### 重要提示

- ⚠️ Cookie 包含敏感信息，请勿泄露
- ⚠️ Cookie 有有效期，过期后需要重新获取
- ⚠️ 建议将 `.env` 添加到 `.gitignore`

## API 文档

启动服务后访问：
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 项目结构

```
MyCrawler/
├── main.py              # FastAPI 入口与路由
├── crawler.py           # Playwright 爬虫核心逻辑
├── utils.py             # 工具函数
├── requirements.txt     # 依赖列表
├── .env.example         # 环境变量模版
├── venv/                # 虚拟环境
├── output/              # 保存的文章目录
└── docs/
    └── 需求文档.md       # 产品需求文档
```

## 许可证

MIT License

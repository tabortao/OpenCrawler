# 项目规则：OpenCrawler - 多平台网页 Markdown 提取 API

## 项目概述

OpenCrawler 是一个模块化的网页内容提取工具，将网页转换为 Markdown 格式。它使用插件架构，通过 FastAPI 提供 REST API 端点，使用 Playwright 进行浏览器自动化。

## 基本要求

- 所有的 Python 测试脚本都放到 test 文件夹
- 每个函数需要有中文注释
- API 遵循 RESTful 规范

## 技术栈

- FastAPI + Playwright + Trafilatura

## 项目结构

```
OpenCrawler/
├── main_new.py              # 新版入口文件（推荐）
├── main.py                  # 原入口文件（兼容）
├── app/
│   ├── api/                 # API 层
│   ├── core/                # 核心模块（配置、异常、依赖注入）
│   ├── crawlers/            # 爬虫核心（基类、工厂、图片下载器）
│   ├── plugins/             # 插件目录（各平台插件）
│   ├── converters/          # 转换器模块（Markdown、图片提取）
│   └── utils/               # 工具模块（URL、文件、文本）
├── test/                    # 测试目录
└── docs/                    # 文档目录
```

## 架构概述

### 核心结构
- **API 层** (`app/api/`): FastAPI 端点，用于页面和文章
- **插件系统** (`app/plugins/`): 平台特定的爬虫（GitHub、知乎、小红书、微信、少数派、通用）
- **核心模块** (`app/core/`): 配置、异常和依赖项
- **爬虫** (`app/crawlers/`): 基础爬虫类和图片下载器
- **转换器** (`app/converters/`): HTML 到 Markdown 转换和图片提取
- **工具** (`app/utils/`): URL 检测、文件操作和文本处理

### 关键设计模式

1. **插件架构**: 每个平台都实现为继承自 `BasePlugin` 的插件
2. **工厂模式**: `CrawlerFactory` 根据 URL 检测创建适当的爬虫
3. **依赖注入**: FastAPI 依赖项用于浏览器会话和配置
4. **异常处理**: 带有结构化错误响应的自定义 `CrawlerException`

## API 列表

### 系统 API

| 方法 | 路径             | 描述     |
| ---- | ---------------- | -------- |
| GET  | `/api/v1/health` | 健康检查 |

### 页面 API

| 方法 | 路径                            | 描述         |
| ---- | ------------------------------- | ------------ |
| GET  | `/api/v1/pages/title?url=<URL>` | 获取网页标题 |
| POST | `/api/v1/pages/extract`         | 提取页面内容 |

### 文章 API

| 方法 | 路径               | 描述                        |
| ---- | ------------------ | --------------------------- |
| POST | `/api/v1/articles` | 创建文章（保存为 Markdown） |

## 平台配置

| 平台       | 选择器                | 特殊处理                                |
| ---------- | --------------------- | --------------------------------------- |
| GitHub     | `.markdown-body`      | 无                                      |
| 知乎       | `.Post-RichText`      | Cookie 注入、标题过滤私信、内容过滤导航 |
| 小红书     | `.note-content`       | Cookie + 代理                           |
| 微信公众号 | `.rich_media_content` | data-src 图片提取                       |
| 少数派     | `article`             | data-original 高清图片                  |
| 通用       | `article, main`       | 自动内容识别                            |

## 环境变量

```
HOST=127.0.0.1
PORT=8000
OUTPUT_DIR=output
PROXY_URL=
ZHIHU_COOKIE=
XHS_COOKIE=
BROWSER_HEADLESS=
API_TOKEN=           # API 认证令牌（可选，不设置则不需要认证）
```

## API 认证

### 认证方式

如果配置了 `API_TOKEN` 环境变量，所有 API 请求都需要携带认证令牌。支持两种认证方式：

#### 1. Bearer Token 方式（推荐）
```bash
curl -H "Authorization: Bearer <your-token>" http://127.0.0.1:8000/api/v1/pages/extract
```

#### 2. X-API-Token 方式
```bash
curl -H "X-API-Token: <your-token>" http://127.0.0.1:8000/api/v1/pages/extract
```

### 生成令牌

使用以下命令生成高强度随机令牌：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 安全建议

1. **令牌强度**: 使用至少 32 字节的随机字符串
2. **文件权限**: 确保 `.env` 文件权限为仅所有者可读写
   - Windows: 右键 -> 属性 -> 安全 -> 高级 -> 禁用继承 -> 仅保留当前用户
   - Linux/Mac: `chmod 600 .env`
3. **定期轮换**: 建议每 90 天更换一次令牌
4. **不要提交**: 确保 `.env` 文件在 `.gitignore` 中
5. **不要记录**: 令牌不会出现在日志或错误信息中

## 开发设置

```bash
# 创建虚拟环境（使用 micromamba，如 README 所示）
micromamba create -p ./venv python=3.11.4
micromamba run -p ./venv pip install -r requirements.txt

# 安装 Playwright 浏览器
micromamba run -p ./venv playwright install chromium

# 设置环境
cp .env.example .env
# 编辑 .env 文件配置 cookies 和设置
```

## 运行命令

```bash
# 启动 FastAPI 服务器
micromamba run -p ./venv python main.py

# 或直接使用 uvicorn
micromamba run -p ./venv uvicorn main:app --host 127.0.0.1 --port 8000

# 使用新版入口（推荐）
micromamba run -p ./venv python main_new.py

# API 文档可在以下地址获取：
# - Swagger UI: http://127.0.0.1:8000/docs
# - ReDoc: http://127.0.0.1:8000/redoc
```

## 测试 API

```bash
# 健康检查（不需要认证）
curl http://127.0.0.1:8000/api/v1/health

# 如果配置了 API_TOKEN，需要在请求头中携带令牌
# 方式1: Bearer Token
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/api/v1/pages/title?url=https://example.com"

# 方式2: X-API-Token
curl -H "X-API-Token: YOUR_TOKEN" "http://127.0.0.1:8000/api/v1/pages/title?url=https://example.com"

# 获取网页标题
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/api/v1/pages/title?url=https://example.com"

# 提取页面内容
curl -X POST http://127.0.0.1:8000/api/v1/pages/extract \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"url": "https://example.com"}'

# 创建文章（不下载图片）
curl -X POST http://127.0.0.1:8000/api/v1/articles \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"url": "https://zhuanlan.zhihu.com/p/123456789"}'

# 创建文章并下载图片
curl -X POST http://127.0.0.1:8000/api/v1/articles \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"url": "https://mp.weixin.qq.com/s/xxx", "download_images": true}'
```

## 测试

```bash
# 运行测试（添加测试文件后）
python -m pytest test/

# 运行特定测试文件
python -m pytest test/test_specific.py
```

## 注意事项

### uvicorn reload 模式问题

**重要**: `main.py` 和 `main_new.py` 中的 `reload=False` 不能改为 `True`！

当使用 `uvicorn.run("main:app", reload=True)` 启动时，uvicorn 会创建一个 reloader 进程来监控文件变化，这会导致：

1. 模块被多次加载
2. 异步任务执行异常 - 爬取请求没有被正确处理
3. 结果为空 - 生成的 Markdown 文件只有标题，没有内容和图片

**解决方案**: 生产环境必须使用 `reload=False`。如果需要开发调试，可以使用测试脚本 `test/test_markdown_conversion.py` 直接测试爬虫功能。

## 插件开发

要添加新平台：
1. 在 `app/plugins/new_platform/` 中创建插件目录
2. 实现 `NewPlatformCrawler`（继承自 `BaseCrawler`）
3. 实现 `NewPlatformPlugin`（继承自 `BasePlugin`）
4. 在 `app/utils/url.py` 中添加 URL 检测逻辑
5. 如有需要，在 `app/core/config.py` 中添加平台配置

## 文件结构导航

常见任务的关键文件：
- **添加新 API 端点**: `app/api/router.py` + 新端点文件
- **添加新平台**: `app/plugins/` 目录
- **修改提取逻辑**: `app/crawlers/base.py` 和平台特定爬虫
- **更改输出格式**: `app/converters/markdown.py`
- **配置更改**: `app/core/config.py`

## 错误处理

应用程序使用结构化错误处理：
- `CrawlerException` 用于爬虫特定错误
- FastAPI 异常处理程序用于一致的 API 响应
- 整个应用程序的日志记录用于调试

## 测试策略

测试目录结构遵循主应用程序结构：
- 单个组件的单元测试
- API 端点的集成测试
- 平台特定功能的插件测试

## 常见开发任务

1. **添加新平台插件**: 遵循现有插件（github、zhihu 等）的模式
2. **修改提取行为**: 更新平台特定爬虫或基础爬虫
3. **API 更改**: 更新 `app/api/` 中的端点并确保正确的请求/响应模型
4. **配置更新**: 在 `app/core/config.py` 中添加新设置
5. **图像处理**: 修改 `app/crawlers/image_downloader.py` 或 `app/converters/image_extractor.py`

## 平台特定经验

- **今日头条图片下载**: 参考 [今日头条图片下载指南](../documents/toutiao_image_download_guide.md) 了解如何处理今日头条的图片下载问题，其他插件开发时可参考本指南。


# OpenCrawler

<div align="center">

**多平台网页 Markdown 提取 API**

基于 FastAPI + Playwright 的网页内容提取服务

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📖 项目简介

OpenCrawler 是一个模块化的网页内容提取工具，能够将网页内容自动转换为 Markdown 格式。采用插件化架构设计，支持多种平台的内容提取，易于扩展和维护。

### ✨ 核心特性

- 🚀 **插件化架构** - 每个平台作为独立插件，支持动态加载
- 📝 **Markdown 转换** - 自动将 HTML 转换为格式化的 Markdown
- 🖼️ **图片处理** - 支持图片下载、本地化和 URL 替换
- 🔐 **Cookie 认证** - 支持需要登录的平台
- 🌐 **RESTful API** - 标准化的 API 接口，易于集成
- 📦 **模块化设计** - 清晰的代码结构，低耦合高内聚

### 🌍 支持的平台

| 平台 | 支持内容 | 特殊处理 |
|------|----------|----------|
| GitHub | 仓库 README、文档 | 无 |
| 知乎 | 文章、回答 | Cookie 注入、内容清理 |
| 小红书 | 笔记内容 | Cookie + 签名验证 |
| 微信公众号 | 文章内容 | 懒加载图片提取 |
| 少数派 | 文章内容 | 高清图片提取 |
| 今日头条 | 文章内容 | 图片 URL 保留、反爬处理 |
| 通用网站 | 任意网页 | 自动内容识别 |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Playwright 浏览器

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/tabortao/OpenCrawler.git
cd OpenCrawler

# 创建虚拟环境
micromamba create -p ./venv python=3.11.4
micromamba run -p ./venv pip install -r requirements.txt

# 安装 Playwright 浏览器
micromamba run -p ./venv playwright install chromium

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要的 Cookie
```

### 启动服务

```bash
micromamba run -p ./venv python main.py
```

服务启动后访问：
- API 文档：http://127.0.0.1:8000/docs
- ReDoc 文档：http://127.0.0.1:8000/redoc

---

## 📚 API 文档

### 系统 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |

### 页面 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/pages/title?url=<URL>` | 获取网页标题 |
| POST | `/api/v1/pages/extract` | 提取页面内容 |

### 文章 API

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/articles` | 创建文章（保存为 Markdown） |

### 使用示例

```bash
# 健康检查（不需要认证）
curl http://127.0.0.1:8000/api/v1/health

# 如果配置了 API_TOKEN，需要在请求头中携带令牌
# 以下示例假设已配置令牌，请将 YOUR_TOKEN 替换为实际令牌

# 获取网页标题
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/api/v1/pages/title?url=https://sspai.com/post/105218"

# 提取页面内容
curl -X POST http://127.0.0.1:8000/api/v1/pages/extract \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"url": "https://sspai.com/post/12345"}'

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

# 创建今日头条文章（保留原始图片 URL）
curl -X POST http://127.0.0.1:8000/api/v1/articles \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"url": "https://www.toutiao.com/article/7611076105369371163", "download_images": true}'
```

---

## 🔧 配置说明

### 环境变量

创建 `.env` 文件并配置以下变量：

```env
# 服务器配置
HOST=127.0.0.1
PORT=8000

# 输出配置
OUTPUT_DIR=output

# 代理配置（可选）
PROXY_URL=

# 平台 Cookie（部分平台需要）
ZHIHU_COOKIE=
XHS_COOKIE=

# 浏览器配置
BROWSER_HEADLESS=

# API 认证令牌（可选，不设置则不需要认证）
API_TOKEN=
```

### API 认证

如果配置了 `API_TOKEN`，所有 API 请求都需要携带认证令牌。

#### 生成令牌

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 使用令牌

支持两种认证方式：

```bash
# 方式1: Bearer Token（推荐）
curl -H "Authorization: Bearer YOUR_TOKEN" http://127.0.0.1:8000/api/v1/pages/extract

# 方式2: X-API-Token
curl -H "X-API-Token: YOUR_TOKEN" http://127.0.0.1:8000/api/v1/pages/extract
```

#### 安全建议

1. 使用至少 32 字节的随机字符串
2. 定期轮换令牌（建议每 90 天）
3. 确保 `.env` 文件不在版本控制中
4. 设置适当的文件权限（Linux/Mac: `chmod 600 .env`）

### Cookie 获取方法

1. **知乎 Cookie**
   - 打开 https://www.zhihu.com 并登录
   - 按 F12 打开开发者工具
   - 在 Application -> Cookies 中复制 Cookie

2. **小红书 Cookie**
   - 打开 https://www.xiaohongshu.com 并登录
   - 按 F12 打开开发者工具
   - 在 Application -> Cookies 中复制 Cookie

---

## 🏗️ 项目结构

```
OpenCrawler/
├── main.py                      # 原入口文件（保留兼容）
├── main_new.py                  # 新版入口文件
├── app/
│   ├── __init__.py
│   ├── api/                     # API 层
│   │   ├── router.py            # 路由注册
│   │   ├── pages.py             # 页面相关 API
│   │   └── articles.py          # 文章相关 API
│   │
│   ├── core/                    # 核心模块
│   │   ├── config.py            # 配置管理
│   │   ├── exceptions.py        # 异常定义
│   │   └── dependencies.py      # 依赖注入
│   │
│   ├── crawlers/                # 爬虫核心
│   │   ├── base.py              # 爬虫基类
│   │   ├── factory.py           # 爬虫工厂
│   │   └── image_downloader.py  # 图片下载器
│   │
│   ├── plugins/                 # 插件目录
│   │   ├── base.py              # 插件基类
│   │   ├── registry.py          # 插件注册中心
│   │   ├── generic/             # 通用插件
│   │   ├── github/              # GitHub 插件
│   │   ├── zhihu/               # 知乎插件
│   │   ├── xiaohongshu/         # 小红书插件
│   │   ├── wechat/              # 微信公众号插件
│   │   ├── sspai/               # 少数派插件
│   │   └── toutiao/             # 今日头条插件
│   │
│   ├── converters/              # 转换器模块
│   │   ├── markdown.py          # Markdown 转换器
│   │   └── image_extractor.py   # 图片提取器
│   │
│   └── utils/                   # 工具模块
│       ├── url.py               # URL 工具
│       ├── file.py              # 文件工具
│       └── text.py              # 文本处理工具
│
├── test/                        # 测试目录
└── docs/                        # 文档目录
```

---

## 🔌 插件开发

### 创建新插件

1. 在 `app/plugins/` 下创建新目录

```python
# app/plugins/new_platform/__init__.py
from .crawler import NewPlatformCrawler, NewPlatformPlugin

__all__ = ["NewPlatformCrawler", "NewPlatformPlugin"]
```

2. 实现插件类

```python
# app/plugins/new_platform/crawler.py
from app.plugins.base import BasePlugin, PluginInfo
from app.crawlers.base import CrawlResult, BaseCrawler


class NewPlatformCrawler(BaseCrawler):
    @property
    def name(self) -> str:
        return "new_platform"
    
    @property
    def platforms(self) -> list[str]:
        return ["new_platform"]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        # 实现爬取逻辑
        pass


class NewPlatformPlugin(BasePlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="new_platform",
            version="1.0.0",
            description="新平台内容提取插件",
            platforms=["new_platform"],
        )
    
    @property
    def platforms(self) -> list[str]:
        return ["new_platform"]
    
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        crawler = NewPlatformCrawler()
        return await crawler.extract(url, **kwargs)
```

3. 在 `app/utils/url.py` 中添加平台检测

```python
def detect_platform(url: str) -> str:
    url_lower = url.lower()
    
    # 添加新平台检测
    if "newplatform.com" in url_lower:
        return "new_platform"
    # ... 其他平台
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [Playwright](https://playwright.dev/python/) - 浏览器自动化工具
- [Trafilatura](https://trafilatura.readthedocs.io/) - Web 内容提取库
- [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) - 架构参考

---

<div align="center">

**OpenCrawler** © 2026 - Present

</div>

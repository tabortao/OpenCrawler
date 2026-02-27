# 项目规则：OpenCrawler - 多平台网页 Markdown 提取 API

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
```

## 运行命令

```bash
# 使用新版入口（推荐）
micromamba run -p ./venv python main_new.py

# 使用原入口（兼容）
micromamba run -p ./venv python main.py
```

## 测试 API

```bash
# 健康检查
curl http://127.0.0.1:8000/api/v1/health

# 获取网页标题
curl "http://127.0.0.1:8000/api/v1/pages/title?url=https://example.com"

# 提取页面内容
curl -X POST http://127.0.0.1:8000/api/v1/pages/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# 创建文章（不下载图片）
curl -X POST http://127.0.0.1:8000/api/v1/articles \
  -H "Content-Type: application/json" \
  -d '{"url": "https://zhuanlan.zhihu.com/p/123456789"}'

# 创建文章并下载图片
curl -X POST http://127.0.0.1:8000/api/v1/articles \
  -H "Content-Type: application/json" \
  -d '{"url": "https://mp.weixin.qq.com/s/xxx", "download_images": true}'
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

参考 `app/plugins/` 目录下的现有插件实现。每个插件需要：

1. 继承 `BasePlugin` 和 `BaseCrawler`
2. 实现 `extract` 方法
3. 在 `__init__.py` 中导出 Plugin 类
4. 在 `app/utils/url.py` 中添加平台检测

## 废弃文件

以下文件已迁移到新模块，可以删除：

- `crawler.py` → `app/crawlers/` 和 `app/plugins/`
- `xhs_crawler.py` → `app/plugins/xiaohongshu/`
- `markdown_converter.py` → `app/converters/markdown.py`
- `utils.py` → `app/utils/`

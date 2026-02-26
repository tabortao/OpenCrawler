# 项目规则：多平台网页 Markdown 提取 API

## 基本要求

- 所有的python测试脚本都放到test文件夹
- 每个函数需要有中文注释
- API 遵循 RESTful 规范

## 技术栈

- FastAPI + Playwright + Trafilatura

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

**重要**: `main.py` 中的 `reload=False` 不能改为 `True`！

当使用 `uvicorn.run("main:app", reload=True)` 启动时，uvicorn 会创建一个 reloader 进程来监控文件变化，这会导致：

1. 模块被多次加载
2. 异步任务执行异常 - 爬取请求没有被正确处理
3. 结果为空 - 生成的 Markdown 文件只有标题，没有内容和图片

**解决方案**: 生产环境必须使用 `reload=False`。如果需要开发调试，可以使用测试脚本 `test/test_markdown_conversion.py` 直接测试爬虫功能。

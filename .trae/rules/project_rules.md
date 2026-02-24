# 项目规则：多平台网页 Markdown 提取 API

## 技术栈
- FastAPI + Playwright + Trafilatura

## API
- `GET /extract?url=<URL>` - 提取网页内容
- `GET /save?url=<URL>&download_images=<true|false>` - 保存为 Markdown 文件

## 平台配置
| 平台 | 选择器 | 特殊处理 |
|------|--------|----------|
| GitHub | `.markdown-body` | 无 |
| 知乎 | `.Post-RichText` | Cookie 注入、标题过滤私信、内容过滤导航 |
| 小红书 | `.note-content` | Cookie + 代理 |
| 微信公众号 | `.rich_media_content` | data-src 图片提取 |

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
curl http://127.0.0.1:8000/health

# 保存文章（不下载图片）
curl "http://127.0.0.1:8000/save?url=https://zhuanlan.zhihu.com/p/123456789"

# 保存文章并下载图片
curl "http://127.0.0.1:8000/save?url=https://mp.weixin.qq.com/s/xxx&download_images=true"
```

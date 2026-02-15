# 项目规则：多平台网页 Markdown 提取 API

## 技术栈
- **框架**: FastAPI (Python 3.10+)
- **爬虫引擎**: Crawlee (Python) + Playwright (Chromium)
- **内容解析**: Trafilatura
- **配置管理**: python-dotenv
- **异步处理**: asyncio & httpx

## 目录结构
```
/project-root
├── .env                    # 环境配置文件
├── .env.example            # 环境配置模版
├── main.py                 # FastAPI 入口与路由
├── crawler.py              # Playwright 核心逻辑与 Cookie 注入
├── utils.py                # Cookie 解析与文本处理工具
├── requirements.txt        # 依赖列表
├── venv/                   # micromamba 虚拟环境目录
└── docs/
    └── 需求文档.md          # 产品需求文档
```

## 编码规范
- 使用 Python 3.10+ 语法特性
- 所有函数必须有类型注解
- 使用 async/await 进行异步编程
- 异常处理要完善，返回标准 HTTP 状态码

## API 规范
### GET /extract
**参数**: `url` (string, required)

**成功响应** (200):
```json
{
  "status": "success",
  "title": "文章标题",
  "url": "原始URL",
  "markdown": "# 转换后的内容..."
}
```

**错误响应**:
- 400: URL 格式不正确
- 422: 页面内容为空或无法解析
- 500: 抓取超时或代理失效

## 平台特定配置
| 平台 | 选择器 | 超时时间 | 特殊处理 |
|------|--------|----------|----------|
| GitHub | `.markdown-body` | 10s | 无 |
| 知乎 | `.Post-RichText` | 15s | Cookie 注入 |
| 小红书 | `.note-content` | 15s | Cookie + 代理 |
| 微信公众号 | `.rich_media_content` | 12s | 过滤广告 |

## 环境变量
- `HOST`: 服务器地址 (默认: 127.0.0.1)
- `PORT`: 服务器端口 (默认: 8000)
- `PROXY_URL`: 代理服务器地址
- `ZHIHU_COOKIE`: 知乎 Cookie 字符串
- `XHS_COOKIE`: 小红书 Cookie 字符串

## 虚拟环境与运行命令

### 使用 micromamba 创建虚拟环境
```bash
# 创建虚拟环境 (Python 3.11)
micromamba create -p ./venv python=3.11 -y

# 安装依赖
micromamba run -p ./venv python -m pip install -r requirements.txt

# 安装 Playwright 浏览器
micromamba run -p ./venv playwright install chromium
```

### 启动服务
```bash
# 启动开发服务器 (带热重载)
micromamba run -p ./venv python main.py

# 或手动激活环境后启动
micromamba activate ./venv
python main.py
```

### 测试 API
```bash
# 健康检查
curl http://127.0.0.1:8000/health

# 提取网页内容
curl "http://127.0.0.1:8000/extract?url=https://github.com/fastapi/fastapi"
```

## 测试命令
```bash
# 类型检查
pyright .

# 代码格式化
ruff format .
```

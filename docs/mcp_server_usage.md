# OpenCrawler MCP Server 使用说明

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
micromamba create -p ./venv python=3.11.4

# 激活虚拟环境并安装依赖
micromamba install -p ./venv -c conda-forge mcp anyio click starlette -y
micromamba run -p ./venv pip install -r requirements.txt

# 安装 Playwright 浏览器
micromamba run -p ./venv playwright install chromium
```

### 2. 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置必要的 Cookie（可选）
# ZHIHU_COOKIE=your_zhihu_cookie
# XHS_COOKIE=your_xiaohongshu_cookie
```

### 3. 启动 MCP 服务器

```bash
# stdio 模式（推荐 Cherry Studio）
micromamba run -p ./venv python mcp_server.py stdio

# SSE 模式（推荐 Cherry Studio HTTP 方式），注意sse和http启动命令是不同的
micromamba run -p ./venv python mcp_server.py sse --port 8765

# HTTP 模式（推荐 Trae、Cursor），注意sse和http启动命令是不同的
micromamba run -p ./venv python mcp_server.py http --port 8765
```

## 三种传输方式对比

| 模式  | 端点          | 适用场景                      | 特点                   |
| ----- | ------------- | ----------------------------- | ---------------------- |
| stdio | 标准输入/输出 | Cherry Studio、Claude Desktop | 本地进程通信，无需端口 |
| sse   | `/sse`        | Cherry Studio (HTTP)          | 服务器推送事件         |
| http  | `/mcp`        | Trae、Cursor                  | Streamable HTTP        |

---

## Cherry Studio 配置

### 方法一：stdio 模式（推荐）

1. 打开 Cherry Studio
2. 进入 **设置** → **MCP 服务器**
3. 确保已安装 **uv** 和 **bun**（按钮显示绿色）
4. 点击 **添加服务器**
5. 选择类型为 **stdio**
6. 填写以下信息：
   - **名称**: `opencrawler`
   - **命令**: `micromamba`
   - **参数**: `run -p F:\Code\Python-Project\OpenCrawler\venv python F:\Code\Python-Project\OpenCrawler\mcp_server.py stdio`

7. 保存配置

### 方法二：SSE 模式

先启动服务器：
```bash
micromamba run -p ./venv python mcp_server.py sse --port 8765
```

然后在 Cherry Studio 中：
1. 选择类型为 **SSE**
2. URL 填写：`http://127.0.0.1:8765/sse`

**SSE 模式工作原理**：
1. 客户端连接 `/sse` 端点
2. 服务器返回消息端点 URL（如 `/messages/?session_id=xxx`）
3. 客户端通过该 URL 发送消息

### 方法三：Streamable HTTP 模式

先启动服务器：

```bash
micromamba run -p ./venv python mcp_server.py http --port 8765
```

然后在 Cherry Studio 中：

1. 选择类型为 **streamableHttp**
2. URL 填写：`http://127.0.0.1:8765/mcp`

### JSON 配置示例

**stdio 模式**:

```json
{
  "mcpServers": {
    "opencrawler": {
      "command": "micromamba",
      "args": [
        "run",
        "-p",
        "F:\\Code\\Python-Project\\OpenCrawler\\venv",
        "python",
        "F:\\Code\\Python-Project\\OpenCrawler\\mcp_server.py",
        "stdio"
      ]
    }
  }
}
```

**SSE 模式**:

```json
{
  "mcpServers": {
    "opencrawler": {
      "type": "sse",
      "url": "http://127.0.0.1:8765/sse"
    }
  }
}
```

**HTTP 模式**:

```json
{
  "mcpServers": {
    "opencrawler": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

### 重要提示

1. **必须使用支持函数调用的模型**：选择模型名称后有 🔧 扳手符号的模型
2. **路径使用绝对路径**：将 `F:\Code\Python-Project\OpenCrawler` 替换为你的实际路径
3. **确保 uv 和 bun 已安装**：在 Cherry Studio 设置中检查

---

## Trae IDE 配置

### 启动 HTTP 服务器

```bash
micromamba run -p ./venv python mcp_server.py http --port 8765
```

### 配置方法

编辑 Trae 的 MCP 配置文件：

**Windows**: `%APPDATA%\Trae\mcp.json`

**macOS**: `~/Library/Application Support/Trae/mcp.json`

**Linux**: `~/.config/Trae/mcp.json`

添加以下配置：

```json
{
  "mcpServers": {
    "opencrawler": {
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

---

## Claude Desktop 配置

### macOS

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "opencrawler": {
      "command": "micromamba",
      "args": [
        "run",
        "-p",
        "/path/to/OpenCrawler/venv",
        "python",
        "/path/to/OpenCrawler/mcp_server.py",
        "stdio"
      ]
    }
  }
}
```

### Windows

编辑 `%APPDATA%\Claude\claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "opencrawler": {
      "command": "micromamba",
      "args": [
        "run",
        "-p",
        "F:\\Code\\Python-Project\\OpenCrawler\\venv",
        "python",
        "F:\\Code\\Python-Project\\OpenCrawler\\mcp_server.py",
        "stdio"
      ]
    }
  }
}
```

---

## 提供的工具

### crawl_webpage

**功能**：抓取网页并转换为 Markdown

**参数**：
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| url | string | 是 | 网页 URL |
| download_images | boolean | 否 | 是否下载图片 |

### extract_content

**功能**：提取网页内容，返回结构化数据

**参数**：
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| url | string | 是 | 网页 URL |

### get_page_title

**功能**：获取网页标题

**参数**：
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| url | string | 是 | 网页 URL |

### save_article

**功能**：保存文章为 Markdown 文件

**参数**：
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| url | string | 是 | 网页 URL |
| download_images | boolean | 否 | 是否下载图片 |
| compress_images | boolean | 否 | 是否压缩图片（需要启用 download_images） |
| compress_quality | integer | 否 | 压缩质量 (1-95)，默认 85 |

### list_platforms

**功能**：列出支持的平台

**参数**：无

---

## 支持的平台

| 平台       | URL 模式           | 特殊说明           |
| ---------- | ------------------ | ------------------ |
| GitHub     | github.com         | 支持 Markdown 渲染 |
| 知乎       | zhuanlan.zhihu.com | 需要配置 Cookie    |
| 小红书     | xiaohongshu.com    | 需要配置 Cookie    |
| 微信公众号 | mp.weixin.qq.com   | 支持图片提取       |
| 少数派     | sspai.com          | 支持高清图片       |
| 今日头条   | toutiao.com        | -                  |
| 通用       | 其他网站           | 自动识别正文       |

---

## 故障排除

### 插件未找到错误

确保在启动服务器前初始化插件。服务器会自动初始化，但如果遇到问题，可以手动测试：

```bash
micromamba run -p ./venv python -c "import asyncio; from app.plugins.registry import initialize_plugins; asyncio.run(initialize_plugins())"
```

### Cherry Studio 无法连接

1. 确保 MCP 服务器正在运行
2. 检查 URL 是否正确
3. 确保选择了支持函数调用的模型（有扳手符号）
4. 检查 uv 和 bun 是否已安装

### 抓取失败

1. 检查 URL 是否有效
2. 检查网络连接
3. 对于需要登录的网站，检查 Cookie 配置

---

## 使用 MCP Inspector 测试

```bash
# 测试 stdio 模式
npx @modelcontextprotocol/inspector python mcp_server.py stdio

# 测试 HTTP 模式
npx @modelcontextprotocol/inspector http://127.0.0.1:8765/mcp
```

---

## 更新日志

### v1.1.0 (2025-02-27)

- 添加 SSE 传输支持
- 修复插件未初始化问题
- 支持三种传输方式：stdio、sse、http

### v1.0.0 (2025-02-27)

- 初始版本发布
- 支持 5 个工具
- 支持 7 个平台

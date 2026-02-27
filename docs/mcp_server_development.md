# OpenCrawler MCP Server 开发文档

## 概述

OpenCrawler MCP Server 是一个符合 MCP (Model Context Protocol) 标准的服务器实现，提供网页内容提取和转换功能。它可以与 Claude Desktop、Trae IDE 等 MCP 兼容的 AI 工具无缝对接。

## MCP 协议简介

MCP (Model Context Protocol) 是 Anthropic 提出的开放标准协议，用于标准化 AI 模型与外部工具和数据源的集成方式。

### 核心概念

1. **Host（宿主）**: AI 应用程序，如 Claude Desktop
2. **Client（客户端）**: 宿主内的连接器
3. **Server（服务器）**: 提供上下文和能力的服务

### 协议特性

- 基于 JSON-RPC 2.0 消息格式
- 支持 stdio 和 HTTP 两种传输方式
- 提供能力协商机制
- 支持 Tools、Resources、Prompts 三种核心功能

## 架构设计

### 模块结构

```
app/mcp/
├── __init__.py          # 模块入口
├── server.py            # MCP 服务器主类
├── protocol.py          # JSON-RPC 协议实现
├── transport.py         # 传输层实现
├── capabilities.py      # 能力协商
├── tools.py             # 工具框架
├── resources.py         # 资源框架
└── prompts.py           # 提示框架

app/mcp_tools/
└── __init__.py          # OpenCrawler 工具实现
```

### 核心组件

#### 1. MCPServer

主服务器类，负责：
- 管理传输层
- 处理协议消息
- 协调各功能模块

```python
from app.mcp.server import MCPServer

server = MCPServer(
    name="MyServer",
    version="1.0.0",
    instructions="服务器使用说明",
)
```

#### 2. ToolRegistry

工具注册表，管理所有可用工具：

```python
from app.mcp.tools import ToolRegistry, ToolInputSchema

@server.tools.register(
    name="my_tool",
    description="工具描述",
    input_schema=ToolInputSchema(
        type="object",
        properties={"url": {"type": "string"}},
        required=["url"],
    ),
)
async def my_tool(url: str):
    return f"处理 {url}"
```

#### 3. ResourceRegistry

资源注册表，管理可访问资源：

```python
@server.resources.register(
    uri="resource://config",
    name="配置信息",
    mime_type="application/json",
)
async def get_config():
    return '{"key": "value"}'
```

#### 4. PromptRegistry

提示注册表，管理提示模板：

```python
@server.prompts.register(
    name="my_prompt",
    description="提示描述",
    arguments=[PromptArgument(name="query", required=True)],
)
async def my_prompt(query: str):
    return PromptResult.user_message(f"查询: {query}")
```

## 提供的工具

### 1. crawl_webpage

抓取网页并转换为 Markdown 格式。

**参数：**
- `url` (必需): 要抓取的网页 URL
- `download_images` (可选): 是否下载图片，默认 false

**返回：**
- 页面标题
- Markdown 格式内容
- 图片 URL 列表

### 2. extract_content

提取网页内容，返回结构化数据。

**参数：**
- `url` (必需): 要提取内容的网页 URL

**返回：**
- title: 页面标题
- markdown: Markdown 内容
- html: HTML 源码
- image_count: 图片数量

### 3. get_page_title

获取网页标题。

**参数：**
- `url` (必需): 网页 URL

**返回：**
- 页面标题

### 4. save_article

保存文章为 Markdown 文件。

**参数：**
- `url` (必需): 网页 URL
- `download_images` (可选): 是否下载图片

**返回：**
- 保存路径
- 文章信息

### 5. list_platforms

列出支持的平台。

**参数：** 无

**返回：**
- 平台列表及其说明

## 提供的资源

### opencrawler://config

当前 OpenCrawler 配置信息。

### opencrawler://platforms

支持的平台列表。

## 提供的提示

### crawl_article

抓取文章的提示模板。

**参数：**
- `url`: 要抓取的网页 URL

### summarize_article

抓取并生成摘要的提示模板。

**参数：**
- `url`: 要抓取的网页 URL

### compare_articles

比较多篇文章的提示模板。

**参数：**
- `urls`: URL 列表（逗号分隔）

## 扩展开发

### 添加新工具

1. 创建工具类：

```python
from app.mcp.tools import BaseTool, ToolInputSchema, ToolResult

class MyCustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_custom_tool"
    
    @property
    def description(self) -> str:
        return "自定义工具描述"
    
    @property
    def input_schema(self) -> ToolInputSchema:
        return ToolInputSchema(
            type="object",
            properties={
                "param1": {"type": "string", "description": "参数1"},
            },
            required=["param1"],
        )
    
    async def execute(self, param1: str) -> ToolResult:
        result = f"处理 {param1}"
        return ToolResult.text(result)
```

2. 注册工具：

```python
from app.mcp_tools import register_opencrawler_tools

def register_opencrawler_tools(registry):
    registry.register_tool(MyCustomTool().to_tool())
```

### 添加新资源

```python
from app.mcp.resources import BaseResource, TextResourceContents

class MyResource(BaseResource):
    @property
    def uri(self) -> str:
        return "my://resource"
    
    @property
    def name(self) -> str:
        return "我的资源"
    
    async def read(self):
        return TextResourceContents(
            uri=self.uri,
            text="资源内容",
        )
```

### 添加新提示

```python
from app.mcp.prompts import BasePrompt, PromptResult, PromptArgument

class MyPrompt(BasePrompt):
    @property
    def name(self) -> str:
        return "my_prompt"
    
    @property
    def arguments(self) -> list[PromptArgument]:
        return [PromptArgument(name="query", required=True)]
    
    async def render(self, query: str) -> PromptResult:
        return PromptResult.user_message(f"查询: {query}")
```

## 错误处理

### 标准错误码

| 错误码 | 说明 |
|--------|------|
| -32700 | JSON 解析错误 |
| -32600 | 无效请求 |
| -32601 | 方法未找到 |
| -32602 | 无效参数 |
| -32603 | 内部错误 |
| -32002 | 资源未找到 |
| -32003 | 资源读取错误 |

### 错误响应示例

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid URL format"
  }
}
```

## 安全考虑

1. **输入验证**: 所有工具参数都经过验证
2. **URL 验证**: 只接受 HTTP/HTTPS 协议的 URL
3. **资源隔离**: 每个客户端连接独立
4. **错误信息**: 不暴露敏感系统信息

## 性能优化

1. **异步处理**: 所有 I/O 操作都是异步的
2. **连接复用**: 浏览器实例可复用
3. **超时控制**: 所有操作都有超时限制

## 日志记录

服务器通过 stderr 输出日志：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
)
```

## 测试

### 手动测试

使用 MCP Inspector 工具：

```bash
npx @modelcontextprotocol/inspector python mcp_server.py
```

### 单元测试

```python
import pytest
from app.mcp.server import MCPServer
from app.mcp.protocol import JSONRPCRequest

@pytest.mark.asyncio
async def test_initialize():
    server = MCPServer()
    
    request = JSONRPCRequest(
        id=1,
        method="initialize",
        params={
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"},
        },
    )
    
    response = await server._handle_initialize(request)
    assert response.error is None
```

## 版本兼容性

| MCP 版本 | 支持状态 |
|----------|----------|
| 2025-03-26 | ✅ 完全支持 |
| 2024-11-05 | ✅ 兼容 |

## 常见问题

### Q: 如何调试 MCP 服务器？

A: 查看 stderr 输出的日志，或使用 MCP Inspector 工具。

### Q: 如何处理需要登录的网站？

A: 在 .env 文件中配置相应的 Cookie。

### Q: 如何限制并发请求？

A: 在工具实现中添加信号量控制。

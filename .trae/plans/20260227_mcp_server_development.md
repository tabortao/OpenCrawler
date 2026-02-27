# MCP Server 开发计划

## 任务概述
为 OpenCrawler 项目开发一个符合 MCP (Model Context Protocol) 标准的 MCP Server 组件，实现与 Claude Desktop 等 AI 工具的无缝对接。

## MCP 协议核心要点

### 1. 基础协议
- 基于 JSON-RPC 2.0 消息格式
- 支持三种消息类型：Request、Response、Notification
- 状态连接，需要能力协商

### 2. 传输方式
- **stdio**: 标准输入/输出通信（推荐）
- **Streamable HTTP**: HTTP POST/GET + SSE 流

### 3. 生命周期
1. **初始化阶段**: 协议版本协商、能力交换
2. **操作阶段**: 正常协议通信
3. **关闭阶段**: 优雅终止连接

### 4. 核心功能
- **Resources**: 暴露资源（文件、数据等）
- **Tools**: 暴露可调用工具
- **Prompts**: 提供提示模板

## 开发任务清单

### 阶段一：核心框架搭建
- [x] 1.1 创建 MCP 模块目录结构
- [x] 1.2 实现 JSON-RPC 2.0 消息处理
- [x] 1.3 实现 stdio 传输层
- [x] 1.4 实现生命周期管理（初始化、操作、关闭）

### 阶段二：核心功能实现
- [x] 2.1 实现 Resources 功能
- [x] 2.2 实现 Tools 功能（集成 OpenCrawler 爬虫）
- [x] 2.3 实现 Prompts 功能
- [x] 2.4 实现能力协商机制

### 阶段三：OpenCrawler 集成
- [x] 3.1 实现网页抓取工具
- [x] 3.2 实现内容提取工具
- [x] 3.3 实现文章保存工具
- [x] 3.4 实现健康检查工具

### 阶段四：安全与错误处理
- [x] 4.1 实现输入验证
- [x] 4.2 实现错误处理机制
- [x] 4.3 实现日志记录
- [x] 4.4 实现超时处理

### 阶段五：文档与测试
- [x] 5.1 编写开发文档
- [x] 5.2 编写使用示例
- [x] 5.3 编写 Claude Desktop 配置指南
- [x] 5.4 进行兼容性测试

## 目录结构设计

```
app/
├── mcp/
│   ├── __init__.py
│   ├── server.py           # MCP Server 主类
│   ├── protocol.py         # JSON-RPC 协议处理
│   ├── transport.py        # 传输层实现
│   ├── lifecycle.py        # 生命周期管理
│   ├── resources.py        # Resources 实现
│   ├── tools.py            # Tools 实现
│   ├── prompts.py          # Prompts 实现
│   └── capabilities.py     # 能力协商
├── mcp_tools/              # OpenCrawler 工具实现
│   ├── __init__.py
│   ├── crawl_tool.py       # 网页抓取工具
│   ├── extract_tool.py     # 内容提取工具
│   └── article_tool.py     # 文章保存工具
```

## OpenCrawler MCP Tools 设计

### 1. crawl_webpage
抓取网页并转换为 Markdown
- 参数: url, download_images
- 返回: Markdown 内容

### 2. extract_content
提取网页内容
- 参数: url
- 返回: 提取的内容

### 3. get_page_title
获取网页标题
- 参数: url
- 返回: 页面标题

### 4. save_article
保存文章为 Markdown 文件
- 参数: url, download_images
- 返回: 保存路径

### 5. list_platforms
列出支持的平台
- 参数: 无
- 返回: 平台列表

## 技术实现要点

1. **JSON-RPC 消息处理**
   - 请求解析和验证
   - 响应构建
   - 错误码映射

2. **stdio 传输**
   - stdin 读取 JSON-RPC 消息
   - stdout 写入响应
   - stderr 日志输出

3. **能力协商**
   - 声明服务器能力
   - 处理客户端能力
   - 动态功能启用

4. **工具调用**
   - 参数验证
   - 异步执行
   - 结果格式化

## 兼容性测试计划

1. Claude Desktop 配置测试
2. MCP Inspector 工具测试
3. 自定义客户端测试

# -*- coding: utf-8 -*-
"""
OpenCrawler MCP Server

支持三种传输方式：
1. stdio - 标准输入/输出（适用于 Cherry Studio、Claude Desktop）
2. sse - 服务器发送事件（适用于 Cherry Studio、Cursor）
3. streamable-http - HTTP 流式传输（适用于 Trae、Cursor）

使用方法：
- stdio 模式: python mcp_server.py stdio
- sse 模式: python mcp_server.py sse --port 8765
- http 模式: python mcp_server.py http --port 8765
"""

import asyncio
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import click
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

SERVER_NAME = "opencrawler"

_plugins_initialized = False


def _ensure_plugins_initialized():
    """确保插件已初始化"""
    global _plugins_initialized
    if not _plugins_initialized:
        from app.plugins.registry import plugin_registry, initialize_plugins
        if not plugin_registry.get_all_plugins():
            asyncio.run(initialize_plugins())
        _plugins_initialized = True


mcp = FastMCP(
    name=SERVER_NAME,
    instructions="""OpenCrawler MCP Server - 网页内容提取工具

本服务器提供以下工具：

1. crawl_webpage - 抓取网页并转换为 Markdown
2. extract_content - 提取网页内容
3. get_page_title - 获取网页标题
4. save_article - 保存文章为 Markdown 文件
5. list_platforms - 列出支持的平台

支持的平台：
- GitHub (github.com)
- 知乎
- 小红书
- 微信公众号
- 少数派
- 今日头条
- 通用网页 (其他网站)
""",
)


def _normalize_url(value: str) -> str:
    """验证并规范化 URL"""
    candidate = value.strip()
    if not candidate:
        raise ValueError("URL 不能为空")
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("请提供包含协议的完整链接")
    return candidate


async def _crawl_url(url: str, download_images: bool = False):
    """异步爬取 URL"""
    _ensure_plugins_initialized()
    from app.crawlers.factory import CrawlerFactory
    return await CrawlerFactory.crawl(url, download_images=download_images)


def _build_crawl_result(result, url: str) -> dict[str, Any]:
    """构建爬取结果"""
    return {
        "status": "success",
        "url": url,
        "title": result.title,
        "markdown": result.markdown,
        "html": result.html[:500] + "..." if len(result.html) > 500 else result.html,
        "image_count": len(result.image_urls),
        "images": result.image_urls[:10],
    }


@mcp.tool(
    name="crawl_webpage",
    title="抓取网页",
    description=(
        "抓取网页内容并转换为 Markdown 格式。\n"
        "支持的平台：GitHub、知乎、小红书、微信公众号、少数派、今日头条、通用网页。\n"
        "参数：\n"
        "- url: 网页链接（必需）\n"
        "- download_images: 是否下载图片（可选，默认 false）"
    ),
)
async def crawl_webpage(url: str, download_images: bool = False) -> dict[str, Any]:
    """
    抓取网页并转换为 Markdown
    
    Args:
        url: 网页 URL
        download_images: 是否下载图片
    
    Returns:
        包含标题、Markdown 内容、图片列表的结果
    """
    normalized_url = _normalize_url(url)
    result = await _crawl_url(normalized_url, download_images)
    
    return {
        "status": "success",
        "url": normalized_url,
        "title": result.title,
        "markdown": result.markdown,
        "image_count": len(result.image_urls),
        "images": result.image_urls,
    }


@mcp.tool(
    name="extract_content",
    title="提取内容",
    description=(
        "从网页中提取主要内容，返回结构化数据。\n"
        "参数：\n"
        "- url: 网页链接（必需）"
    ),
)
async def extract_content(url: str) -> dict[str, Any]:
    """
    提取网页内容
    
    Args:
        url: 网页 URL
    
    Returns:
        结构化的内容数据
    """
    normalized_url = _normalize_url(url)
    result = await _crawl_url(normalized_url)
    
    return _build_crawl_result(result, normalized_url)


@mcp.tool(
    name="get_page_title",
    title="获取标题",
    description="获取网页的标题。这是一个轻量级操作，适合快速检查网页。",
)
async def get_page_title(url: str) -> dict[str, Any]:
    """
    获取网页标题
    
    Args:
        url: 网页 URL
    
    Returns:
        页面标题
    """
    normalized_url = _normalize_url(url)
    result = await _crawl_url(normalized_url)
    
    return {
        "status": "success",
        "url": normalized_url,
        "title": result.title or "无标题",
    }


@mcp.tool(
    name="save_article",
    title="保存文章",
    description=(
        "抓取网页并保存为 Markdown 文件。\n"
        "文件保存到 output 目录。\n"
        "参数：\n"
        "- url: 网页链接（必需）\n"
        "- download_images: 是否下载图片（可选，默认 false）"
    ),
)
async def save_article(url: str, download_images: bool = False) -> dict[str, Any]:
    """
    保存文章为 Markdown 文件
    
    Args:
        url: 网页 URL
        download_images: 是否下载图片
    
    Returns:
        保存结果
    """
    from app.core.config import settings
    
    normalized_url = _normalize_url(url)
    result = await _crawl_url(normalized_url, download_images)
    
    output_dir = settings.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", result.title)
    safe_title = safe_title[:100]
    
    filename = f"{today}_{safe_title}.md"
    filepath = os.path.join(output_dir, filename)
    
    counter = 1
    while os.path.exists(filepath):
        filename = f"{today}_{safe_title}_{counter}.md"
        filepath = os.path.join(output_dir, filename)
        counter += 1
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {result.title}\n\n")
        f.write(f"**来源**: {normalized_url}\n\n")
        f.write("---\n\n")
        f.write(result.markdown)
    
    return {
        "status": "success",
        "url": normalized_url,
        "title": result.title,
        "filepath": filepath,
        "image_count": len(result.image_urls),
    }


@mcp.tool(
    name="list_platforms",
    title="列出平台",
    description="列出 OpenCrawler 支持的所有平台及其特点。",
)
async def list_platforms() -> dict[str, Any]:
    """
    列出支持的平台
    
    Returns:
        平台列表
    """
    _ensure_plugins_initialized()
    from app.plugins.registry import plugin_registry
    
    platforms = plugin_registry.get_supported_platforms()
    
    platform_info = {
        "github": {"name": "GitHub", "description": "GitHub 仓库和 Gist，支持 Markdown 渲染"},
        "zhihu": {"name": "知乎", "description": "知乎专栏文章，需要登录 Cookie"},
        "xiaohongshu": {"name": "小红书", "description": "小红书笔记，需要登录 Cookie"},
        "wechat": {"name": "微信公众号", "description": "微信公众号文章，支持图片提取"},
        "sspai": {"name": "少数派", "description": "少数派文章，支持高清图片"},
        "toutiao": {"name": "今日头条", "description": "今日头条文章"},
        "generic": {"name": "通用网页", "description": "通用网页，自动识别正文内容"},
    }
    
    result = []
    for platform in platforms:
        info = platform_info.get(platform, {"name": platform, "description": "通用支持"})
        result.append({
            "id": platform,
            "name": info["name"],
            "description": info["description"],
        })
    
    return {
        "status": "success",
        "platforms": result,
        "total": len(result),
    }


@mcp.resource("platforms://list", title="支持的平台")
def platforms_resource() -> str:
    """平台列表资源"""
    _ensure_plugins_initialized()
    from app.plugins.registry import plugin_registry
    
    platforms = plugin_registry.get_supported_platforms()
    
    lines = ["# OpenCrawler 支持的平台", ""]
    for p in platforms:
        lines.append(f"- **{p}**")
    
    lines.append("")
    lines.append("## 使用说明")
    lines.append("")
    lines.append("1. 对于需要登录的平台（知乎、小红书），请在 .env 文件中配置 Cookie")
    lines.append("2. 通用模式支持大多数网站，会自动提取正文内容")
    lines.append("3. 所有平台都支持图片提取和下载")
    
    return "\n".join(lines)


@mcp.resource("config://current", title="当前配置")
def config_resource() -> str:
    """当前配置资源"""
    from app.core.config import settings
    import json
    
    config_data = {
        "host": settings.host,
        "port": settings.port,
        "output_dir": settings.output_dir,
        "browser_headless": settings.browser_headless,
        "platforms": list(settings.platforms.keys()),
    }
    
    return json.dumps(config_data, ensure_ascii=False, indent=2)


def run_http_server(host: str, port: int, path: str):
    """运行 Streamable HTTP 服务器"""
    import uvicorn
    
    _ensure_plugins_initialized()
    
    mcp.settings.streamable_http_path = path
    app = mcp.streamable_http_app()
    
    @app.route("/health", methods=["GET"])
    async def health(request: Request) -> Response:
        return JSONResponse({"status": "ok", "name": SERVER_NAME})
    
    uvicorn.run(app, host=host, port=port, log_level="info")


def run_sse_server(host: str, port: int):
    """运行 SSE 服务器"""
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    
    _ensure_plugins_initialized()
    
    sse_app = mcp.sse_app()
    
    routes = [
        Route("/health", endpoint=lambda request: JSONResponse({"status": "ok", "name": SERVER_NAME}), methods=["GET"]),
    ]
    
    for route in sse_app.routes:
        routes.append(route)
    
    app = Starlette(routes=routes)
    
    uvicorn.run(app, host=host, port=port, log_level="info")


def run_stdio_server():
    """运行 stdio 服务器"""
    _ensure_plugins_initialized()
    mcp.run(transport="stdio")


@click.command()
@click.argument("mode", default="stdio", type=click.Choice(["stdio", "sse", "http"]))
@click.option("--host", default="127.0.0.1", show_default=True, help="绑定的主机地址 (sse/http 模式)")
@click.option("--port", default=8765, show_default=True, help="HTTP 端口 (sse/http 模式)")
@click.option("--path", default="/mcp", show_default=True, help="MCP 路径 (http 模式)")
def main(mode: str, host: str, port: int, path: str) -> None:
    """
    启动 MCP 服务器
    
    模式：
    - stdio: 标准输入/输出模式（适用于 Cherry Studio、Claude Desktop）
    - sse: SSE 模式（适用于 Cherry Studio、Cursor）
    - http: Streamable HTTP 模式（适用于 Trae、Cursor）
    
    示例：
    - stdio 模式: python mcp_server.py stdio
    - sse 模式: python mcp_server.py sse --port 8765
    - http 模式: python mcp_server.py http --port 8765
    """
    if mode == "stdio":
        print("Starting OpenCrawler MCP Server in stdio mode...", file=sys.stderr)
        run_stdio_server()
    elif mode == "sse":
        print(f"Starting OpenCrawler MCP Server in SSE mode on http://{host}:{port}/sse", file=sys.stderr)
        run_sse_server(host, port)
    else:
        print(f"Starting OpenCrawler MCP Server in HTTP mode on http://{host}:{port}{path}", file=sys.stderr)
        run_http_server(host, port, path)


if __name__ == "__main__":
    main()

"""
OpenCrawler MCP 工具模块

提供 OpenCrawler 爬虫功能的 MCP 工具实现。
"""

import os
import re
from typing import Optional

from app.mcp.tools import (
    Tool,
    ToolRegistry,
    ToolInputSchema,
    ToolAnnotation,
    ToolResult,
    BaseTool,
)
from app.mcp.resources import Resource, ResourceRegistry, TextResourceContents
from app.mcp.prompts import Prompt, PromptRegistry, PromptArgument, PromptResult


class CrawlWebpageTool(BaseTool):
    """网页抓取工具"""
    
    @property
    def name(self) -> str:
        return "crawl_webpage"
    
    @property
    def description(self) -> str:
        return """抓取网页内容并转换为 Markdown 格式。
        
支持的平台包括：
- GitHub (github.com)
- 知乎 (zhuanlan.zhihu.com)
- 小红书 (xiaohongshu.com)
- 微信公众号 (mp.weixin.qq.com)
- 少数派 (sspai.com)
- 今日头条 (toutiao.com)
- 通用网页 (其他网站)

返回内容包括：
- 页面标题
- Markdown 格式的正文内容
- 图片 URL 列表"""
    
    @property
    def input_schema(self) -> ToolInputSchema:
        return ToolInputSchema(
            type="object",
            properties={
                "url": {
                    "type": "string",
                    "description": "要抓取的网页 URL（必须是有效的 HTTP/HTTPS URL）",
                },
                "download_images": {
                    "type": "boolean",
                    "description": "是否下载图片到本地（默认为 false）",
                },
            },
            required=["url"],
        )
    
    @property
    def annotations(self) -> Optional[ToolAnnotation]:
        return ToolAnnotation(
            title="网页抓取",
            read_only_hint=True,
            open_world_hint=True,
        )
    
    async def execute(self, url: str, download_images: bool = False) -> ToolResult:
        """
        执行网页抓取
        
        Args:
            url: 网页 URL
            download_images: 是否下载图片
        
        Returns:
            抓取结果
        """
        from app.crawlers.factory import CrawlerFactory
        from app.utils.url import is_valid_url
        
        if not is_valid_url(url):
            return ToolResult.error(f"无效的 URL: {url}")
        
        try:
            result = await CrawlerFactory.crawl(
                url,
                download_images=download_images,
            )
            
            output = f"""# {result.title}

**URL**: {result.url}

---

{result.markdown}

---
"""
            if result.image_urls:
                output += f"\n**图片数量**: {len(result.image_urls)}\n"
            
            return ToolResult.text(output)
            
        except Exception as e:
            return ToolResult.error(f"抓取失败: {str(e)}")


class ExtractContentTool(BaseTool):
    """内容提取工具"""
    
    @property
    def name(self) -> str:
        return "extract_content"
    
    @property
    def description(self) -> str:
        return """从网页中提取主要内容，返回结构化的提取结果。

返回内容包括：
- 页面标题
- Markdown 正文
- HTML 源码
- 图片 URL 列表"""
    
    @property
    def input_schema(self) -> ToolInputSchema:
        return ToolInputSchema(
            type="object",
            properties={
                "url": {
                    "type": "string",
                    "description": "要提取内容的网页 URL",
                },
            },
            required=["url"],
        )
    
    @property
    def annotations(self) -> Optional[ToolAnnotation]:
        return ToolAnnotation(
            title="内容提取",
            read_only_hint=True,
            open_world_hint=True,
        )
    
    async def execute(self, url: str) -> ToolResult:
        """
        执行内容提取
        
        Args:
            url: 网页 URL
        
        Returns:
            提取结果
        """
        from app.crawlers.factory import CrawlerFactory
        from app.utils.url import is_valid_url
        
        if not is_valid_url(url):
            return ToolResult.error(f"无效的 URL: {url}")
        
        try:
            result = await CrawlerFactory.crawl(url)
            
            import json
            output = json.dumps({
                "title": result.title,
                "url": result.url,
                "markdown": result.markdown,
                "html": result.html[:500] + "..." if len(result.html) > 500 else result.html,
                "image_count": len(result.image_urls),
                "images": result.image_urls[:10],
            }, ensure_ascii=False, indent=2)
            
            return ToolResult.text(output)
            
        except Exception as e:
            return ToolResult.error(f"提取失败: {str(e)}")


class GetPageTitleTool(BaseTool):
    """获取页面标题工具"""
    
    @property
    def name(self) -> str:
        return "get_page_title"
    
    @property
    def description(self) -> str:
        return "获取网页的标题。这是一个轻量级操作，适合用于快速检查网页或获取基本信息。"
    
    @property
    def input_schema(self) -> ToolInputSchema:
        return ToolInputSchema(
            type="object",
            properties={
                "url": {
                    "type": "string",
                    "description": "要获取标题的网页 URL",
                },
            },
            required=["url"],
        )
    
    @property
    def annotations(self) -> Optional[ToolAnnotation]:
        return ToolAnnotation(
            title="获取标题",
            read_only_hint=True,
            open_world_hint=True,
        )
    
    async def execute(self, url: str) -> ToolResult:
        """
        执行获取标题
        
        Args:
            url: 网页 URL
        
        Returns:
            标题结果
        """
        from app.crawlers.factory import CrawlerFactory
        from app.utils.url import is_valid_url
        
        if not is_valid_url(url):
            return ToolResult.error(f"无效的 URL: {url}")
        
        try:
            result = await CrawlerFactory.crawl(url)
            
            if result.title:
                return ToolResult.text(f"页面标题: {result.title}\nURL: {url}")
            else:
                return ToolResult.text(f"该页面没有标题\nURL: {url}")
                
        except Exception as e:
            return ToolResult.error(f"获取标题失败: {str(e)}")


class SaveArticleTool(BaseTool):
    """保存文章工具"""
    
    @property
    def name(self) -> str:
        return "save_article"
    
    @property
    def description(self) -> str:
        return """抓取网页并保存为 Markdown 文件。

将网页内容保存到 output 目录，文件名根据标题自动生成。
可以选择是否下载图片到本地。"""
    
    @property
    def input_schema(self) -> ToolInputSchema:
        return ToolInputSchema(
            type="object",
            properties={
                "url": {
                    "type": "string",
                    "description": "要保存的网页 URL",
                },
                "download_images": {
                    "type": "boolean",
                    "description": "是否下载图片到本地（默认为 false）",
                },
            },
            required=["url"],
        )
    
    @property
    def annotations(self) -> Optional[ToolAnnotation]:
        return ToolAnnotation(
            title="保存文章",
            read_only_hint=False,
            destructive_hint=False,
            open_world_hint=True,
        )
    
    async def execute(self, url: str, download_images: bool = False) -> ToolResult:
        """
        执行保存文章
        
        Args:
            url: 网页 URL
            download_images: 是否下载图片
        
        Returns:
            保存结果
        """
        from app.crawlers.factory import CrawlerFactory
        from app.utils.url import is_valid_url
        from app.core.config import settings
        
        if not is_valid_url(url):
            return ToolResult.error(f"无效的 URL: {url}")
        
        try:
            result = await CrawlerFactory.crawl(
                url,
                download_images=download_images,
            )
            
            output_dir = settings.output_dir
            os.makedirs(output_dir, exist_ok=True)
            
            safe_title = re.sub(r'[\\/*?:"<>|]', "_", result.title)
            safe_title = safe_title[:100]
            
            filename = f"{safe_title}.md"
            filepath = os.path.join(output_dir, filename)
            
            counter = 1
            while os.path.exists(filepath):
                filename = f"{safe_title}_{counter}.md"
                filepath = os.path.join(output_dir, filename)
                counter += 1
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {result.title}\n\n")
                f.write(f"**来源**: {result.url}\n\n")
                f.write("---\n\n")
                f.write(result.markdown)
            
            output = f"""文章已保存成功！

**标题**: {result.title}
**文件**: {filepath}
**URL**: {result.url}
**图片数量**: {len(result.image_urls)}
"""
            
            return ToolResult.text(output)
            
        except Exception as e:
            return ToolResult.error(f"保存失败: {str(e)}")


class ListPlatformsTool(BaseTool):
    """列出支持的平台工具"""
    
    @property
    def name(self) -> str:
        return "list_platforms"
    
    @property
    def description(self) -> str:
        return "列出 OpenCrawler 支持的所有平台及其特点。"
    
    @property
    def input_schema(self) -> ToolInputSchema:
        return ToolInputSchema(type="object", properties={})
    
    @property
    def annotations(self) -> Optional[ToolAnnotation]:
        return ToolAnnotation(
            title="列出平台",
            read_only_hint=True,
            open_world_hint=False,
        )
    
    async def execute(self) -> ToolResult:
        """执行列出平台"""
        from app.crawlers.factory import CrawlerFactory
        
        platforms = CrawlerFactory.get_supported_platforms()
        
        platform_info = {
            "github": "GitHub 仓库和 Gist，支持 Markdown 渲染",
            "zhihu": "知乎专栏文章，需要登录 Cookie",
            "xiaohongshu": "小红书笔记，需要登录 Cookie",
            "wechat": "微信公众号文章，支持图片提取",
            "sspai": "少数派文章，支持高清图片",
            "toutiao": "今日头条文章",
            "generic": "通用网页，自动识别正文内容",
        }
        
        output = "# OpenCrawler 支持的平台\n\n"
        for platform in platforms:
            info = platform_info.get(platform, "通用支持")
            output += f"- **{platform}**: {info}\n"
        
        output += "\n## 使用说明\n\n"
        output += "1. 对于需要登录的平台（知乎、小红书），请在 .env 文件中配置 Cookie\n"
        output += "2. 通用模式支持大多数网站，会自动提取正文内容\n"
        output += "3. 所有平台都支持图片提取和下载\n"
        
        return ToolResult.text(output)


def register_opencrawler_tools(registry: ToolRegistry):
    """
    注册 OpenCrawler 工具到注册表
    
    Args:
        registry: 工具注册表
    """
    registry.register_tool(CrawlWebpageTool().to_tool())
    registry.register_tool(ExtractContentTool().to_tool())
    registry.register_tool(GetPageTitleTool().to_tool())
    registry.register_tool(SaveArticleTool().to_tool())
    registry.register_tool(ListPlatformsTool().to_tool())


def register_opencrawler_resources(registry: ResourceRegistry):
    """
    注册 OpenCrawler 资源到注册表
    
    Args:
        registry: 资源注册表
    """
    async def get_config_resource():
        from app.core.config import settings
        import json
        
        config_data = {
            "host": settings.host,
            "port": settings.port,
            "output_dir": settings.output_dir,
            "browser_headless": settings.browser_headless,
            "platforms": list(settings.platforms.keys()),
        }
        
        return TextResourceContents(
            uri="opencrawler://config",
            text=json.dumps(config_data, ensure_ascii=False, indent=2),
            mime_type="application/json",
        )
    
    registry.register_resource(
        Resource(
            uri="opencrawler://config",
            name="OpenCrawler 配置",
            description="当前 OpenCrawler 的配置信息",
            mime_type="application/json",
        ),
        get_config_resource,
    )
    
    async def get_platforms_resource():
        from app.crawlers.factory import CrawlerFactory
        import json
        
        platforms = CrawlerFactory.get_supported_platforms()
        
        return TextResourceContents(
            uri="opencrawler://platforms",
            text=json.dumps({"platforms": platforms}, ensure_ascii=False, indent=2),
            mime_type="application/json",
        )
    
    registry.register_resource(
        Resource(
            uri="opencrawler://platforms",
            name="支持的平台",
            description="OpenCrawler 支持的平台列表",
            mime_type="application/json",
        ),
        get_platforms_resource,
    )


def register_opencrawler_prompts(registry: PromptRegistry):
    """
    注册 OpenCrawler 提示到注册表
    
    Args:
        registry: 提示注册表
    """
    @registry.register(
        name="crawl_article",
        description="抓取网页文章并转换为 Markdown 格式的提示模板",
        arguments=[
            PromptArgument(name="url", description="要抓取的网页 URL", required=True),
        ],
    )
    async def crawl_article_prompt(url: str) -> PromptResult:
        return PromptResult.user_message(
            f"""请帮我抓取以下网页的内容：

{url}

要求：
1. 提取文章标题和正文内容
2. 转换为 Markdown 格式
3. 列出文章中的所有图片链接"""
        )
    
    @registry.register(
        name="summarize_article",
        description="抓取网页并生成摘要的提示模板",
        arguments=[
            PromptArgument(name="url", description="要抓取的网页 URL", required=True),
        ],
    )
    async def summarize_article_prompt(url: str) -> PromptResult:
        return PromptResult.user_message(
            f"""请帮我抓取以下网页并生成摘要：

{url}

要求：
1. 首先抓取网页内容
2. 生成一段 200 字以内的摘要
3. 提取 3-5 个关键词"""
        )
    
    @registry.register(
        name="compare_articles",
        description="抓取并比较多篇文章的提示模板",
        arguments=[
            PromptArgument(name="urls", description="要比较的文章 URL 列表（用逗号分隔）", required=True),
        ],
    )
    async def compare_articles_prompt(urls: str) -> PromptResult:
        url_list = [u.strip() for u in urls.split(",")]
        
        messages = [(
            "user",
            f"""请帮我抓取并比较以下 {len(url_list)} 篇文章：

{chr(10).join(f'{i+1}. {u}' for i, u in enumerate(url_list))}

要求：
1. 分别抓取每篇文章的内容
2. 总结每篇文章的核心观点
3. 比较文章之间的异同点"""
        )]
        
        return PromptResult.conversation(messages)

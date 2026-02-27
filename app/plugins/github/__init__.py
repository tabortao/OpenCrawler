"""
GitHub 插件

支持 GitHub 仓库 README 等内容的提取
"""

from .crawler import GitHubCrawler, GitHubPlugin

__all__ = ["GitHubCrawler", "GitHubPlugin"]

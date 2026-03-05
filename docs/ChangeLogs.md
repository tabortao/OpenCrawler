
## [Todo]

### v2.0.6 / 2026-03-04
- 新增 API 令牌认证功能，保护 API 端点安全：
  - 支持两种认证方式：Bearer Token 和 X-API-Token
  - 使用 `secrets.compare_digest` 进行安全的令牌比较，防止时序攻击
  - 令牌不记录在日志或错误信息中
  - 可选认证：不配置 API_TOKEN 则不需要认证
  - 健康检查端点不需要认证
- 更新项目文档，添加认证方式说明和安全建议
- 修复标题清理正则表达式过于宽泛导致标题被截断的问题
- 新增 Docker 支持：
  - 多阶段构建 Dockerfile，优化镜像体积
  - 支持 linux/amd64 和 linux/arm64 平台
  - 提供 docker-compose.yml 快速部署
  - GitHub Action 自动构建和推送镜像到 Docker Hub 和 GHCR
  - 支持飞牛 NAS 部署

### v2.0.5 / 2026-03-04
- 通用插件全面优化增强，达到与微信公众号、少数派插件同等水平的文章爬取效果：
  - 引入 trafilatura 智能内容提取作为兜底方案
  - 扩展内容选择器列表（从 10 个增加到 20+ 个），支持更多网站结构
  - 实现内容选择器评分系统，智能选择最佳内容区域
  - 增强动态内容处理，支持 SPA 页面内容等待
  - 改进懒加载图片处理，支持更多 data-* 属性和 srcset
  - 智能标题提取（支持 Open Graph、Twitter Card、Schema.org 元数据）
  - 增强内容清理（移除导航、侧边栏、广告、评论、相关文章等无关内容）
  - 新增样板文字自动移除功能
  - 增强 MarkdownConverter 通用图片处理（优先使用 data-original 高清图）
  - 增强 ImageExtractor 图片提取（支持 10+ 种懒加载属性、srcset、CSS 背景图）
  - 改进 HTML 清理，移除残留标签
  - 添加测试脚本验证优化效果
 - 安装 Pillow 库，修复图片压缩功能不生效的问题

## v2.0.4 / 2026-03-03
- 新增图片压缩功能，支持 JPEG、PNG、WebP 格式压缩，节省存储空间。
- API 和 MCP 都支持 `compress_images` 和 `compress_quality` 参数。
- 新增 [图片压缩使用指南](图片压缩使用指南.md) 文档。
- feat(图片压缩): 添加 GIF 格式支持并优化压缩逻辑

## v2.0.3 / 2026-02-27
- MCP调用生成的Markdown文件名，需要和curl调用生成的一致，都为日期+标题。
- 下载的图片，按日期+时间+自增计数器重命名，保存到images目录下的年文件夹、月文件夹下面，例如 `images/2026/02/20260227_143025_001.jpg`，对应的文章Markdown中正确的调用图片路径。
- 修复 `asyncio.run() cannot be called from a running event loop` 错误，在 FastAPI 异步环境中正确处理图片下载。

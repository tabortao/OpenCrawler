
## v2.0.4 / 2026-02-27
- 新增图片压缩功能，支持 JPEG、PNG、WebP 格式压缩，节省存储空间。
- API 和 MCP 都支持 `compress_images` 和 `compress_quality` 参数。
- 新增 [图片压缩使用指南](图片压缩使用指南.md) 文档。

## v2.0.3 / 2026-02-27
- MCP调用生成的Markdown文件名，需要和curl调用生成的一致，都为日期+标题。
- 下载的图片，按日期+时间+自增计数器重命名，保存到images目录下的年文件夹、月文件夹下面，例如 `images/2026/02/20260227_143025_001.jpg`，对应的文章Markdown中正确的调用图片路径。
- 修复 `asyncio.run() cannot be called from a running event loop` 错误，在 FastAPI 异步环境中正确处理图片下载。

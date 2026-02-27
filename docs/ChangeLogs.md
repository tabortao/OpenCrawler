
## v2.0.3 / 2026-02-27
- MCP调用生成的Markdown文件名，需要和curl调用生成的一致，都为日期+标题。
- 下载的图片，按日期+时间+自增计数器重命名，保存到images目录下的年文件夹、月文件夹下面，例如 `images/2026/02/20260227_143025_001.jpg`，对应的文章Markdown中正确的调用图片路径。
- 修复 `asyncio.run() cannot be called from a running event loop` 错误，在 FastAPI 异步环境中正确处理图片下载。

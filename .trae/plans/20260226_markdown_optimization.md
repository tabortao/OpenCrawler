# Markdown 排版优化任务计划

## 任务概述
参考 article-downloader 项目，优化 MyCrawler 项目的 Markdown 文章排版，重点改进微信公众号文章的转换效果。

## 问题分析

### article-downloader 的优势
1. **清晰的文档结构**：标题 -> 作者 -> 发布时间 -> 分隔线 -> 正文 -> 来源链接
2. **精细的 HTML 转换**：标题、强调、代码、链接、图片、列表、引用、表格都有专门处理
3. **彻底的清理**：HTML 实体解码、多余空行清理、行首行尾空格清理
4. **微信公众号特殊处理**：data-src 图片提取、特定标签清理

### MyCrawler 当前问题
1. 使用 `markdownify` 库转换，对某些格式处理不够精细
2. 缺少微信公众号特定格式的深度处理
3. 文档排版可能存在多余空行和格式混乱

## 优化方案

### 1. 增强 markdown_converter.py
- 添加更精细的 HTML 元素转换
- 添加 HTML 实体解码
- 添加微信公众号特定处理（data-src 图片、特殊标签清理）

### 2. 改进 crawler.py 的 save_article 函数
- 优化文档头部格式
- 改进正文排版

### 3. 添加内容清理函数
- 清理多余空行
- 清理行首行尾空格
- 规范化段落间距

## 执行步骤

- [x] 分析 article-downloader 项目实现
- [x] 分析 MyCrawler 当前实现
- [x] 创建优化后的 markdown_converter.py
- [x] 更新 crawler.py 的 save_article 函数
- [x] 测试下载指定微信公众号文章

## 优化结果

### 主要改进
1. **重写 HTML 到 Markdown 转换逻辑**：使用递归方式处理各种 HTML 标签
2. **添加 HTML 实体解码**：正确处理 `&nbsp;`、`&copy;` 等特殊字符
3. **优化微信公众号内容清理**：移除视频播放器、导航栏等无关内容
4. **改进文档结构**：参考 article-downloader 的文档格式（标题 -> 发布时间 -> 分隔线 -> 正文 -> 来源链接）
5. **修复代码块格式**：正确处理 `<pre><code>` 标签

### 测试结果
- 测试 URL: https://mp.weixin.qq.com/s/FRAzFpgRkHYKFb3EnpkxGQ
- 标题: Obsidian + CC：我如何用AI 打造知识管理系统+年度规划
- Markdown 长度: 6321 字符
- 图片数量: 10 张（全部下载成功）
- 输出文件: output/2026-02-26_Obsidian_+_CC：我如何用AI_打造知识管理系统+年度规划.md

### 文件变更
1. `markdown_converter.py` - 重写 HTML 到 Markdown 转换逻辑
2. `crawler.py` - 添加微信公众号内容清理函数，优化 save_article 函数
3. `test/test_wechat_article.py` - 新增测试脚本

# 少数派网站图片下载修复计划

## 问题描述
少数派网站 (sspai.com) 的文章图片无法下载，需要修复图片下载功能。

## 任务列表
- [x] 创建任务计划文件
- [x] 分析少数派网站的图片处理逻辑
- [x] 定位图片下载失败的原因
- [x] 修复图片下载功能
- [x] 测试验证修复效果

## 问题分析

### 发现的问题
1. **图片 URL 提取问题**：少数派使用 `data-original` 属性存储高清原图，而现有代码只检查 `data-src` 和 `src` 属性
2. **图片处理参数问题**：图片 URL 包含 `?imageView2/2/format/webp` 等处理参数，需要移除才能获取原始图片
3. **CDN 防盗链问题**：少数派的图片 CDN 需要设置 `Referer: https://sspai.com/` 才能下载

### 修复方案

#### 1. 修改 `utils.py`
- 添加 `sspai` 平台识别
- 添加少数派平台配置

#### 2. 修改 `markdown_converter.py`
- 在 `extract_images_from_html` 函数中添加 `data-original` 属性支持
- 在 `_convert_element_to_markdown` 函数中添加 `data-original` 属性支持
- 移除图片 URL 中的处理参数
- 添加 `_process_sspai_content` 函数处理少数派内容

#### 3. 修改 `crawler.py`
- 在 `ImageDownloader.download_image` 方法中根据图片 URL 动态设置 Referer

## 修改的文件

### 1. `utils.py`
```python
# 添加少数派平台识别
elif "sspai.com" in url_lower:
    return "sspai"

# 添加少数派平台配置
"sspai": {
    "selector": "article, .article-content, .content",
    "timeout": 15000,
    "scroll_times": 3,
},
```

### 2. `markdown_converter.py`
- `extract_images_from_html`: 添加 `data-original` 属性优先级，移除图片处理参数
- `_convert_element_to_markdown`: 添加 `data-original` 属性支持
- `_process_wechat_content`: 添加 `data-original` 属性支持
- `_process_sspai_content`: 新增函数处理少数派内容

### 3. `crawler.py`
- `ImageDownloader.download_image`: 根据图片 URL 动态设置 Referer

## 测试结果

### 测试命令
```bash
curl -X POST http://127.0.0.1:8000/api/v1/articles -H "Content-Type: application/json" -d '{"url": "https://sspai.com/post/106488", "download_images": true}'
```

### 测试结果
- ✅ 图片成功下载到 `output/images/` 目录
- ✅ Markdown 文件中的图片链接已替换为本地路径
- ✅ 共下载 11 张正文图片

## 总结
成功修复了少数派网站图片下载问题，主要修改包括：
1. 支持 `data-original` 属性提取高清原图
2. 移除图片 URL 中的处理参数
3. 添加 Referer 请求头绕过 CDN 防盗链

# 今日头条图片下载指南

## 问题背景

在开发今日头条爬虫插件时，遇到了图片下载失败的问题。今日头条采用了严格的反爬机制，导致直接下载图片时返回 403 错误。

## 问题分析

1. **图片 URL 结构**：今日头条的图片 URL 包含签名和过期时间等参数，需要完整的 URL 才能访问。
2. **反爬机制**：今日头条对图片请求进行了严格的反爬限制，直接请求会返回 403 错误。
3. **请求头要求**：需要模拟真实浏览器的请求头才能成功下载图片。

## 解决方案

### 1. 完整 URL 处理

- **保留查询参数**：不要移除图片 URL 中的查询参数，这些参数包含访问图片所需的签名和过期时间。
- **处理相对 URL**：确保 URL 是完整的，对于以 `//` 开头的 URL，添加 `https:` 前缀。

### 2. 请求头优化

为今日头条图片请求添加以下请求头：

```python
headers = {
    "Referer": "https://www.toutiao.com/",
    "Origin": "https://www.toutiao.com",
    "Sec-Fetch-Dest": "image",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
```

### 3. 备用方案

- **使用完整图片 URL**：如果从页面中提取的图片 URL 下载失败，可以尝试使用用户提供的完整图片 URL（包含所有参数）。
- **错误处理**：当图片下载失败时，保留原始图片 URL，确保 Markdown 中仍然能正确显示图片。

### 4. 代码实现

在 `app/api/articles.py` 中添加备用图片下载逻辑：

```python
# 对于今日头条，尝试使用用户提供的完整图片 URL
if platform == "toutiao":
    backup_img_url = "完整的图片 URL 包含所有参数"
    local_path = downloader.download_image(backup_img_url)
    if local_path:
        # 替换所有图片 URL
        for img_url in extracted_urls:
            url_mapping[img_url] = local_path
```

## 最佳实践

1. **平台特定处理**：为每个平台添加专门的图片处理逻辑，根据平台的特点调整下载策略。
2. **请求头模拟**：模拟真实浏览器的请求头，减少被反爬的概率。
3. **错误处理**：添加健壮的错误处理机制，确保即使图片下载失败，也能提供合理的降级方案。
4. **调试信息**：添加详细的调试信息，便于排查问题。

## 示例代码

### 图片下载器修改

```python
def download_image(self, url: str) -> Optional[str]:
    # 对于今日头条图片，使用特殊的请求头
    if "toutiao" in clean_url:
        headers["Referer"] = "https://www.toutiao.com/"
        headers["Origin"] = "https://www.toutiao.com"
        # 添加其他请求头
    # 下载逻辑...
```

### 图片 URL 替换

```python
def html_to_markdown_with_images(html: str, image_urls: list[str], output_dir: str, platform: str = "generic") -> str:
    # 尝试下载图片
    # 如果失败，尝试使用备用 URL
    # 替换图片 URL
```

## 总结

今日头条图片下载需要特殊处理，主要是因为其严格的反爬机制和复杂的 URL 结构。通过模拟真实浏览器的请求头、保留完整的 URL 参数以及添加备用下载方案，可以成功下载今日头条的图片。

在开发其他平台的爬虫插件时，可以借鉴这些经验，根据平台的特点调整图片下载策略，确保图片能够正确下载和显示。
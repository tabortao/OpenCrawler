# 任务计划：统一文件名格式和图片命名规则

## 任务背景

1. MCP调用生成的Markdown文件名需要和curl调用生成的一致，都为日期+标题
2. 下载的图片需要按毫秒级时间戳+自增计数器重命名，保存到images目录下的年/月文件夹

## 当前状态

| 项目 | 当前格式 | 目标格式 |
|------|----------|----------|
| MCP文件名 | `{标题}.md` | `{YYYY-MM-DD}_{标题}.md` |
| curl文件名 | `{YYYY-MM-DD}_{标题}.md` | 已符合 |
| 图片保存路径 | `images/{hash}.jpg` | `images/{年}/{月}/{时间戳}_{计数器}.jpg` |

## 任务清单

- [x] 1. 分析当前Markdown文件名生成逻辑（MCP vs curl调用）
- [x] 2. 分析当前图片下载和命名逻辑
- [x] 3. 修改 mcp_server.py 中的文件名生成逻辑，添加日期前缀
- [x] 4. 修改 image_downloader.py 中的图片命名和保存路径逻辑
- [x] 5. 更新 Markdown 中图片路径引用（已自动处理）
- [x] 6. 测试验证修改效果

## 修改详情

### 1. mcp_server.py 修改

在 `save_article` 函数中添加日期前缀：
```python
from datetime import datetime

today = datetime.now().strftime("%Y-%m-%d")
safe_title = re.sub(r'[\\/*?:"<>|]', "_", result.title)
safe_title = safe_title[:100]

filename = f"{today}_{safe_title}.md"
```

### 2. image_downloader.py 修改

- 添加年月子目录结构
- 使用毫秒级时间戳+自增计数器命名
- 格式：`images/2026/02/1734256789123_5678.jpg`

```python
import time

# 初始化时
self._image_counter = 0

# 生成文件名时
timestamp = int(time.time() * 1000)  # 毫秒级时间戳
self._image_counter += 1
filename = f"{timestamp}_{self._image_counter:04d}{ext}"

# 年月子目录
year = datetime.now().strftime("%Y")
month = datetime.now().strftime("%m")
sub_dir = os.path.join(self.images_dir, year, month)
os.makedirs(sub_dir, exist_ok=True)
```

## 预期结果

1. MCP和curl调用生成的Markdown文件名格式一致：`2026-02-27_文章标题.md`
2. 图片保存路径：`images/2026/02/1734256789123_0001.jpg`
3. Markdown中图片引用：`![描述](images/2026/02/1734256789123_0001.jpg)`

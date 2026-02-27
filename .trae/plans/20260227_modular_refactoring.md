# 模块化重构任务计划

## 任务概述

对 MyCrawler 项目进行系统性的模块化重构，采用模块化设计方法并参考 MediaCrawler 项目的架构模式。

## 目标

1. 按照功能职责将现有代码拆分为独立的 Python 文件
2. 设计清晰的模块间接口，建立明确的依赖关系
3. 实现插件化架构，支持不同网站的爬取功能作为独立插件
4. 建立统一的插件注册与管理机制
5. 制定模块命名规范、代码风格标准
6. 确保重构后代码通过所有测试，性能不低于重构前

## 目标架构设计

```
MyCrawler/
├── main.py                      # 应用入口（简化）
├── main_new.py                  # 新版入口文件
├── app/
│   ├── __init__.py
│   ├── api/                     # API 层
│   │   ├── __init__.py
│   │   ├── router.py            # 路由注册
│   │   ├── pages.py             # 页面相关 API
│   │   └── articles.py          # 文章相关 API
│   │
│   ├── core/                    # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py            # 配置管理
│   │   ├── exceptions.py        # 异常定义
│   │   └── dependencies.py      # 依赖注入
│   │
│   ├── crawlers/                # 爬虫核心
│   │   ├── __init__.py
│   │   ├── base.py              # 爬虫基类
│   │   ├── factory.py           # 爬虫工厂
│   │   └── image_downloader.py  # 图片下载器
│   │
│   ├── plugins/                 # 插件目录
│   │   ├── __init__.py
│   │   ├── base.py              # 插件基类
│   │   ├── registry.py          # 插件注册中心
│   │   ├── github/              # GitHub 插件
│   │   │   ├── __init__.py
│   │   │   └── crawler.py
│   │   ├── zhihu/               # 知乎插件
│   │   │   ├── __init__.py
│   │   │   └── crawler.py
│   │   ├── xiaohongshu/         # 小红书插件
│   │   │   ├── __init__.py
│   │   │   └── crawler.py
│   │   ├── wechat/              # 微信公众号插件
│   │   │   ├── __init__.py
│   │   │   └── crawler.py
│   │   └── ssspai/              # 少数派插件
│   │       ├── __init__.py
│   │       └── crawler.py
│   │
│   ├── converters/              # 转换器模块
│   │   ├── __init__.py
│   │   ├── base.py              # 转换器基类
│   │   ├── markdown.py          # Markdown 转换器
│   │   └── image_extractor.py   # 图片提取器
│   │
│   └── utils/                   # 工具模块
│       ├── __init__.py
│       ├── url.py               # URL 工具
│       ├── file.py              # 文件工具
│       └── text.py              # 文本处理工具
│
├── test/                        # 测试目录（保持不变）
└── docs/                        # 文档目录
```

## 任务清单

### 阶段一：基础架构搭建

- [x] 1.1 创建 app 目录结构
- [x] 1.2 实现核心配置模块 (app/core/config.py)
- [x] 1.3 实现异常定义模块 (app/core/exceptions.py)
- [x] 1.4 实现依赖注入模块 (app/core/dependencies.py)

### 阶段二：爬虫核心模块

- [x] 2.1 实现爬虫基类 (app/crawlers/base.py)
- [x] 2.2 实现图片下载器 (app/crawlers/image_downloader.py)
- [x] 2.3 实现爬虫工厂 (app/crawlers/factory.py)

### 阶段三：插件系统

- [x] 3.1 实现插件基类 (app/plugins/base.py)
- [x] 3.2 实现插件注册中心 (app/plugins/registry.py)
- [x] 3.3 实现 GitHub 插件
- [x] 3.4 实现知乎插件
- [x] 3.5 实现小红书插件
- [x] 3.6 实现微信公众号插件
- [x] 3.7 实现少数派插件

### 阶段四：转换器模块

- [x] 4.1 实现转换器基类 (app/converters/base.py)
- [x] 4.2 实现 Markdown 转换器 (app/converters/markdown.py)
- [x] 4.3 实现图片提取器 (app/converters/image_extractor.py)

### 阶段五：工具模块

- [x] 5.1 实现 URL 工具 (app/utils/url.py)
- [x] 5.2 实现文件工具 (app/utils/file.py)
- [x] 5.3 实现文本处理工具 (app/utils/text.py)

### 阶段六：API 层重构

- [x] 6.1 实现路由注册 (app/api/router.py)
- [x] 6.2 实现页面 API (app/api/pages.py)
- [x] 6.3 实现文章 API (app/api/articles.py)
- [x] 6.4 重构主入口文件 (main_new.py)

### 阶段七：测试与验证

- [x] 7.1 模块导入测试通过
- [ ] 7.2 运行现有测试确保功能正常
- [ ] 7.3 性能对比测试

## 设计原则

1. **单一职责原则**：每个模块专注于单一功能
2. **开闭原则**：对扩展开放，对修改关闭
3. **依赖倒置原则**：高层模块不依赖低层模块，两者都依赖抽象
4. **接口隔离原则**：使用小接口而非大接口
5. **迪米特法则**：最少知识原则

## 插件接口设计

```python
class BasePlugin(ABC):
    """插件基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass
    
    @property
    @abstractmethod
    def platforms(self) -> list[str]:
        """支持的平台列表"""
        pass
    
    @abstractmethod
    async def extract(self, url: str, **kwargs) -> CrawlResult:
        """提取内容"""
        pass
    
    def get_content_selector(self) -> str:
        """获取内容选择器"""
        return ""
```

## 进度追踪

| 阶段 | 状态 | 完成时间 |
|------|------|----------|
| 基础架构搭建 | ✅ 完成 | 2026-02-27 |
| 爬虫核心模块 | ✅ 完成 | 2026-02-27 |
| 插件系统 | ✅ 完成 | 2026-02-27 |
| 转换器模块 | ✅ 完成 | 2026-02-27 |
| 工具模块 | ✅ 完成 | 2026-02-27 |
| API 层重构 | ✅ 完成 | 2026-02-27 |
| 测试与验证 | 🔄 进行中 | - |

## 注意事项

1. 保持向后兼容，确保现有 API 接口不变
2. 所有函数必须有中文注释
3. 遵循 RESTful API 规范
4. uvicorn reload=False 不能修改
5. 新入口文件为 main_new.py，待测试通过后可替换 main.py

## 后续工作

1. 运行完整测试套件验证功能
2. 性能对比测试
3. 更新项目文档
4. 考虑添加更多平台插件

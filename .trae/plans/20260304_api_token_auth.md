# API 令牌认证功能实现计划

## 任务目标
为 OpenCrawler 项目添加 API 令牌认证功能，确保只有授权用户才能访问 API。

## 需求分析

### 核心功能
1. 在 .env 文件中配置 API 令牌
2. 通过 curl 或 MCP 访问 API 时必须在请求头中包含令牌
3. 系统验证令牌与配置的是否一致
4. 只有验证通过的请求才能访问

### 安全增强措施
1. 设置 .env 文件权限为仅所有者可读写
2. 令牌采用高强度随机字符串
3. 令牌不在代码仓库、日志或错误信息中明文显示
4. 支持令牌轮换

## 实施步骤

### 1. 配置层修改
- 在 `app/core/config.py` 中添加 API_TOKEN 配置项
- 在 `.env.example` 中添加令牌配置示例
- 在 `.env` 中生成并配置高强度随机令牌

### 2. 认证中间件
- 创建 `app/core/auth.py` 模块
- 实现令牌验证依赖项
- 返回标准化的认证错误响应

### 3. API 路由更新
- 在 `app/api/router.py` 中添加认证依赖
- 对所有需要保护的端点添加认证

### 4. 文档更新
- 更新 `project_rules.md` 说明认证方式
- 更新 `.env.example` 添加令牌配置说明

### 5. 安全措施
- 提供 .env 文件权限设置脚本
- 确保令牌不记录在日志中

## 文件修改清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/core/config.py` | 修改 | 添加 API_TOKEN 配置 |
| `app/core/auth.py` | 新建 | 令牌验证模块 |
| `app/api/router.py` | 修改 | 添加认证依赖 |
| `.env.example` | 修改 | 添加令牌示例 |
| `.env` | 修改 | 配置实际令牌 |
| `docs/快速使用本项目.md` | 修改 | 添加认证说明 |

## API 认证方式

### 请求头方式
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/pages/extract
```

### 或使用 X-API-Token 方式
```bash
curl -H "X-API-Token: <token>" http://localhost:8000/api/v1/pages/extract
```

## 预期成果
- 所有 API 端点都需要令牌认证
- 未授权请求返回 401 错误
- 令牌不暴露在日志和错误信息中
- 文档清晰说明认证方式

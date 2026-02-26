## RESTful API 规范

**重要**: 所有新增 API 必须遵循 RESTful 规范！

### URL 设计规范

1. **使用名词而非动词**
   - ✅ 正确: `POST /api/v1/articles`
   - ❌ 错误: `POST /api/v1/create-article`

2. **使用复数形式**
   - ✅ 正确: `/api/v1/pages`, `/api/v1/articles`
   - ❌ 错误: `/api/v1/page`, `/api/v1/article`

3. **使用版本控制**
   - ✅ 正确: `/api/v1/...`
   - ❌ 错误: `/api/...`

4. **资源层级清晰**
   - `/api/v1/pages/title` - 获取页面标题
   - `/api/v1/pages/extract` - 提取页面内容
   - `/api/v1/articles` - 文章资源

### HTTP 方法规范

| 方法 | 用途 | 示例 |
|------|------|------|
| GET | 获取资源 | `GET /api/v1/pages/title?url=xxx` |
| POST | 创建资源 | `POST /api/v1/articles` |
| PUT | 更新资源（完整） | `PUT /api/v1/articles/123` |
| PATCH | 更新资源（部分） | `PATCH /api/v1/articles/123` |
| DELETE | 删除资源 | `DELETE /api/v1/articles/123` |

### HTTP 状态码规范

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未授权（Cookie 过期等） |
| 404 | Not Found | 资源不存在（标题不存在等） |
| 422 | Unprocessable Entity | 语义错误（内容为空等） |
| 500 | Internal Server Error | 服务器内部错误 |
| 504 | Gateway Timeout | 请求超时 |

### 响应格式规范

**成功响应**:
```json
{
  "title": "文章标题",
  "url": "https://example.com",
  "markdown": "..."
}
```

**错误响应**:
```json
{
  "error": "ERROR_CODE",
  "message": "错误详情描述"
}
```

**禁止使用**:
- ❌ 不要在响应中包含 `status` 字段，使用 HTTP 状态码表示
- ❌ 不要在响应中包含 `success: true/false`
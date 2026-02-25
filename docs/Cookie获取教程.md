# Cookie 获取教程

本文档介绍如何获取知乎和小红书的 Cookie，并配置到 `.env` 文件中。

## 目录

- [方法一：浏览器开发者工具（推荐）](#方法一浏览器开发者工具推荐)
- [方法二：使用 EditThisCookie 扩展](#方法二使用-editthiscookie-扩展)
- [Cookie 格式说明](#cookie-格式说明)
- [配置到 .env 文件](#配置到-env-文件)
- [常见问题](#常见问题)

---

## 方法一：浏览器开发者工具（推荐）

### 知乎 Cookie 获取

#### 步骤 1：登录知乎

1. 打开浏览器（Chrome / Edge / Firefox）
2. 访问 [知乎首页](https://www.zhihu.com)
3. 使用手机号、微信或其他方式登录

#### 步骤 2：打开开发者工具

- **Chrome / Edge**: 按 `F12` 或 `Ctrl+Shift+I`（Mac: `Cmd+Option+I`）
- **Firefox**: 按 `F12` 或 `Ctrl+Shift+K`

#### 步骤 3：切换到 Network 标签

1. 点击开发者工具顶部的 **Network**（网络）标签
2. 如果列表为空，刷新页面（`F5`）

#### 步骤 4：找到请求并复制 Cookie

1. 点击列表中的任意请求（如第一个）
2. 在右侧面板中找到 **Headers**（标头）
3. 向下滚动找到 **Request Headers** 部分
4. 找到 `Cookie:` 行
5. 复制整个 Cookie 值（可能很长，需要全部复制）

![知乎 Cookie 获取示意](./images/zhihu-cookie.png)

#### 步骤 5：配置到 .env

```env
ZHIHU_COOKIE=_zap=xxx; d_c0=xxx; q_c1=xxx; ...
```

---

### 小红书 Cookie 获取

#### 步骤 1：登录小红书

1. 打开浏览器
2. 访问 [小红书首页](https://www.xiaohongshu.com)
3. 使用手机号或其他方式登录

#### 步骤 2-5：同知乎步骤

操作步骤与知乎相同：

1. 按 `F12` 打开开发者工具
2. 切换到 **Network** 标签
3. 刷新页面
4. 找到请求的 **Headers** → **Request Headers**
5. 复制 `Cookie` 值

#### 步骤 6：配置到 .env

```env
XHS_COOKIE=a1=xxx; webId=xxx; web_session=xxx; ...
```

---

## 方法二：使用 EditThisCookie 扩展

### 安装扩展

**Chrome / Edge:**

1. 访问 [Chrome 网上应用店](https://chrome.google.com/webstore/detail/editthiscookie/)
2. 点击 "添加至 Chrome"

**Firefox:**

1. 访问 [Firefox Add-ons](https://addons.mozilla.org/firefox/addon/editthiscookie/)

### 导出 Cookie

1. 访问目标网站并登录
2. 点击浏览器工具栏中的 EditThisCookie 图标
3. 点击 **Export**（导出）按钮
4. Cookie 会以 JSON 格式复制到剪贴板

### 转换格式

EditThisCookie 导出的是 JSON 格式，需要转换为字符串格式：

**JSON 格式示例:**
```json
[
  {"name": "a1", "value": "xxx", "domain": ".xiaohongshu.com"},
  {"name": "webId", "value": "xxx", "domain": ".xiaohongshu.com"}
]
```

**转换为字符串格式:**
```
a1=xxx; webId=xxx
```

---

## Cookie 格式说明

### 标准格式

Cookie 字符串格式为：
```
name1=value1; name2=value2; name3=value3
```

多个 Cookie 之间用 `; `（分号+空格）分隔。

### 知乎重要 Cookie 字段

| 字段名 | 说明 | 必需 |
|--------|------|------|
| `d_c0` | 设备标识 | 是 |
| `q_c1` | 请求标识 | 是 |
| `_zap` | 防爬标识 | 推荐 |
| `z_c0` | 登录凭证（登录后有） | 登录必需 |

### 小红书重要 Cookie 字段

| 字段名 | 说明 | 必需 |
|--------|------|------|
| `a1` | 设备标识 | 是 |
| `webId` | Web 标识 | 是 |
| `web_session` | 会话标识 | 是 |
| `websectiga` | 登录凭证（登录后有） | 登录必需 |

---

## 配置到 .env 文件

### 1. 复制模板文件

```bash
cp .env.example .env
```

### 2. 编辑 .env 文件

打开 `.env` 文件，找到对应行并粘贴 Cookie：

```env
# 服务器配置
HOST=127.0.0.1
PORT=8000

# 输出目录
OUTPUT_DIR=output

# 代理配置（可选）
PROXY_URL=

# 知乎 Cookie（必填，否则无法抓取知乎内容）
ZHIHU_COOKIE=_zap=xxx; d_c0=AQAwBw; q_c1=xxx; Hm_lvt_98beee=123456

# 小红书 Cookie（必填，否则无法抓取小红书内容）
XHS_COOKIE=a1=xxx; webId=xxx; web_session=xxx; websectiga=xxx
```

### 3. 重启服务

修改 `.env` 后需要重启服务：

```bash
# 停止当前服务（Ctrl+C）
# 重新启动
micromamba run -p ./venv python main.py
```

---

## 常见问题

### Q1: Cookie 有多长？

Cookie 可能很长（几百到几千字符），这是正常的。请确保完整复制。

### Q2: Cookie 会过期吗？

是的，Cookie 有有效期：
- **知乎**: 通常 7-30 天
- **小红书**: 通常 **几小时到 1-2 天**（非常短）

过期后需要重新获取并更新 `.env` 文件。

### Q3: 如何判断 Cookie 是否有效？

1. 启动服务后调用 API
2. 如果返回 `EMPTY_CONTENT` 错误，可能是 Cookie 过期
3. 重新获取 Cookie 并更新

### Q4: 小红书 Cookie 特别注意事项

⚠️ **小红书 Cookie 有效期非常短**，建议：

1. **获取后立即使用** - 不要等太久
2. **使用完整 Cookie** - 确保包含 `websectiga`、`id_token`、`web_session` 等关键字段
3. **避免频繁请求** - 可能导致 Cookie 被封禁
4. **检查登录状态** - 在浏览器中确认已登录后再获取 Cookie

**获取小红书 Cookie 的最佳时机：**
- 刚登录成功后立即获取
- 在浏览器中能正常浏览笔记时获取
- 避免在登录页面获取（此时 Cookie 不完整）

### Q4: Cookie 安全吗？

⚠️ **重要提示:**

- Cookie 包含敏感信息，**请勿分享给他人**
- 不要将 `.env` 文件提交到 Git 仓库
- 项目已将 `.env` 添加到 `.gitignore`

### Q5: 为什么需要 Cookie？

知乎和小红书需要登录才能查看完整内容：
- 未登录：只能看到部分内容或被重定向
- 已登录（有 Cookie）：可以访问完整内容

### Q6: 抓取频率有限制吗？

是的，建议：
- 控制请求频率，避免短时间内大量请求
- 使用代理分散请求
- 遵守网站的 robots.txt 和服务条款

---

## 快速参考

### 知乎 Cookie 获取流程

```
1. 访问 zhihu.com 并登录
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 刷新页面
5. 点击任意请求 → Headers → Request Headers
6. 复制 Cookie 值
7. 粘贴到 .env 的 ZHIHU_COOKIE=
```

### 小红书 Cookie 获取流程

```
1. 访问 xiaohongshu.com 并登录
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 刷新页面
5. 点击任意请求 → Headers → Request Headers
6. 复制 Cookie 值
7. 粘贴到 .env 的 XHS_COOKIE=
```

---

## 相关链接

- [知乎官网](https://www.zhihu.com)
- [小红书官网](https://www.xiaohongshu.com)
- [EditThisCookie 扩展](https://chrome.google.com/webstore/detail/editthiscookie/)

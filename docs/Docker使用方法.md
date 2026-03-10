# OpenCrawler Docker 使用指南

本文档详细介绍 OpenCrawler 项目的 Docker 部署和使用方法。

---

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [Dockerfile 说明](#dockerfile-说明)
- [Docker Compose 配置](#docker-compose-配置)
- [镜像构建](#镜像构建)
- [容器管理](#容器管理)
- [数据持久化](#数据持久化)
- [网络配置](#网络配置)
- [多环境配置](#多环境配置)
- [常见问题](#常见问题)

---

## 环境要求

### 软件要求

| 软件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Docker | 20.10+ | 24.0+ |
| Docker Compose | 2.0+ | 2.20+ |

### 硬件要求

| 资源 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 1 核 | 2 核+ |
| 内存 | 1 GB | 2 GB+ |
| 磁盘 | 1 GB | 5 GB+ |

### 安装 Docker

#### Linux (Ubuntu/Debian)

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose
sudo apt-get install docker-compose-plugin

# 添加当前用户到 docker 组
sudo usermod -aG docker $USER

# 验证安装
docker --version
docker compose version
```

#### macOS

```bash
# 使用 Homebrew 安装
brew install --cask docker

# 或下载 Docker Desktop
# https://www.docker.com/products/docker-desktop
```

#### Windows

1. 下载 [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. 运行安装程序
3. 启动 Docker Desktop

#### 飞牛 NAS

飞牛 NAS 通常已预装 Docker，可直接使用。

---

## 快速开始

### 方式1：Docker Compose（推荐）

```bash
# 1. 创建项目目录
mkdir opencrawler && cd opencrawler

# 2. 下载配置文件
curl -O https://raw.githubusercontent.com/tabortao/OpenCrawler/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/tabortao/OpenCrawler/main/.env.docker.example
cp .env.docker.example .env

# 3. 编辑配置文件
vim .env

# 4. 启动服务
docker compose up -d

# 5. 查看日志
docker compose logs -f

# 6. 验证服务
curl http://localhost:8000/api/v1/health
```

### 方式2：手动运行容器

```bash
# 1. 拉取镜像
docker pull ghcr.io/tabortao/opencrawler:latest

# 2. 创建目录
mkdir -p output data

# 3. 运行容器
docker run -d \
  --name opencrawler \
  -p 8000:8000 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/data:/app/data \
  -e API_TOKEN=your_secure_token \
  --restart unless-stopped \
  ghcr.io/tabortao/opencrawler:latest

# 4. 验证服务
curl http://localhost:8000/api/v1/health
```

---

## Dockerfile 说明

### 完整 Dockerfile

```dockerfile
# 阶段1: 构建阶段 - 安装依赖
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 预安装 Playwright 浏览器（仅 chromium）
RUN playwright install chromium --with-deps

# 阶段2: 运行阶段 - 最小化镜像
FROM python:3.11-slim-bookworm

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    libatspi2.0-0 libxshmfence1 curl \
    && rm -rf /var/lib/apt/lists/*

# 复制虚拟环境和浏览器
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

ENV PATH="/opt/venv/bin:$PATH"
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# 创建用户和目录
RUN useradd -m -u 1000 appuser
RUN mkdir -p /app/output /app/data && chown -R appuser:appuser /app

# 复制应用代码
COPY --chown=appuser:appuser . .

USER appuser
EXPOSE 8000 8765

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["python", "main.py"]
```

### 构建阶段说明

| 阶段 | 说明 |
|------|------|
| builder | 安装编译依赖、Python 包、Playwright 浏览器 |
| runtime | 复制必要文件，配置运行环境 |

### 优化策略

1. **多阶段构建**：分离构建和运行环境，减小镜像体积
2. **slim 基础镜像**：使用 `python:3.11-slim-bookworm`
3. **仅安装 chromium**：Playwright 只安装必要浏览器
4. **清理缓存**：删除 apt 缓存减少体积
5. **非 root 用户**：使用 appuser 运行，提高安全性

---

## Docker Compose 配置

### 完整配置文件

```yaml
version: '3.8'

services:
  # API 服务 - 提供 REST API
  opencrawler-api:
    image: ghcr.io/tabortao/opencrawler:latest
    container_name: opencrawler-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - API_TOKEN=${API_TOKEN:-}
      - BROWSER_HEADLESS=true
      - ZHIHU_COOKIE=${ZHIHU_COOKIE:-}
      - XHS_COOKIE=${XHS_COOKIE:-}
      - PROXY_URL=${PROXY_URL:-}
    volumes:
      - ./output:/app/output
      - ./data:/app/data
      - browser_data:/app/browser_data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    command: ["python", "main.py"]

  # MCP 服务 - 提供 MCP Server（可选）
  opencrawler-mcp:
    image: ghcr.io/tabortao/opencrawler:latest
    container_name: opencrawler-mcp
    restart: unless-stopped
    ports:
      - "8765:8765"
    environment:
      - BROWSER_HEADLESS=true
      - ZHIHU_COOKIE=${ZHIHU_COOKIE:-}
      - XHS_COOKIE=${XHS_COOKIE:-}
      - PROXY_URL=${PROXY_URL:-}
    volumes:
      - ./output:/app/output
      - ./data:/app/data
      - browser_data:/app/browser_data
    command: ["python", "mcp_server.py", "http", "--host", "0.0.0.0", "--port", "8765"]
    profiles:
      - mcp

volumes:
  browser_data:
```

### 配置项说明

#### 服务配置

| 配置项 | 说明 |
|--------|------|
| `image` | 使用的镜像 |
| `container_name` | 容器名称 |
| `restart` | 重启策略 |
| `ports` | 端口映射 |
| `environment` | 环境变量 |
| `volumes` | 数据卷挂载 |
| `healthcheck` | 健康检查 |
| `command` | 启动命令 |
| `profiles` | 服务配置文件 |

#### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HOST` | 监听地址 | `0.0.0.0` |
| `PORT` | API 端口 | `8000` |
| `API_TOKEN` | 认证令牌 | 空 |
| `BROWSER_HEADLESS` | 无头模式 | `true` |
| `ZHIHU_COOKIE` | 知乎 Cookie | - |
| `XHS_COOKIE` | 小红书 Cookie | - |
| `PROXY_URL` | 代理地址 | - |

---

## 镜像构建

### 从源码构建

```bash
# 克隆项目
git clone https://github.com/tabortao/OpenCrawler.git
cd OpenCrawler

# 构建镜像
docker build -t opencrawler:local .

# 构建并指定标签
docker build -t opencrawler:v2.0.6 -t opencrawler:latest .

# 构建时传递参数
docker build --build-arg PYTHON_VERSION=3.11 -t opencrawler:local .
```

### 构建参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `PYTHON_VERSION` | Python 版本 | `3.11` |

### 多平台构建

```bash
# 设置 buildx
docker buildx create --use

# 构建多平台镜像
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t opencrawler:latest \
  --push \
  .
```

---

## 容器管理

### 启动容器

```bash
# 使用 docker compose
docker compose up -d                    # 启动 API 服务
docker compose --profile mcp up -d      # 启动 API + MCP 服务

# 使用 docker run
docker run -d --name opencrawler \
  -p 8000:8000 \
  -v $(pwd)/output:/app/output \
  opencrawler:latest
```

### 停止容器

```bash
# 使用 docker compose
docker compose stop                     # 停止服务
docker compose down                     # 停止并移除容器

# 使用 docker
docker stop opencrawler
docker rm opencrawler
```

### 重启容器

```bash
# 使用 docker compose
docker compose restart

# 使用 docker
docker restart opencrawler
```

### 查看日志

```bash
# 查看所有日志
docker compose logs

# 实时查看日志
docker compose logs -f

# 查看最近 100 行日志
docker compose logs --tail 100

# 查看特定服务日志
docker compose logs opencrawler-api

# 使用 docker
docker logs opencrawler
docker logs -f --tail 100 opencrawler
```

### 进入容器

```bash
# 进入容器 shell
docker compose exec opencrawler-api bash

# 执行单个命令
docker compose exec opencrawler-api python -c "print('hello')"

# 使用 docker
docker exec -it opencrawler bash
```

### 查看容器状态

```bash
# 查看运行状态
docker compose ps

# 查看资源使用
docker stats opencrawler

# 查看详细信息
docker inspect opencrawler
```

---

## 数据持久化

### 目录映射

| 容器路径 | 宿主机路径 | 说明 |
|----------|------------|------|
| `/app/output` | `./output` | Markdown 文件输出 |
| `/app/data` | `./data` | 配置和数据文件 |
| `/app/browser_data` | 命名卷 | 浏览器数据（Cookie） |

### 数据卷类型

#### 绑定挂载（Bind Mount）

```yaml
volumes:
  - ./output:/app/output
  - ./data:/app/data
```

#### 命名卷（Named Volume）

```yaml
volumes:
  - browser_data:/app/browser_data

volumes:
  browser_data:
```

### 数据备份

```bash
# 备份 output 目录
tar -czf opencrawler-backup-$(date +%Y%m%d).tar.gz output/ data/

# 备份命名卷
docker run --rm -v opencrawler_browser_data:/data -v $(pwd):/backup alpine tar -czf /backup/browser_data.tar.gz /data
```

### 数据恢复

```bash
# 恢复 output 目录
tar -xzf opencrawler-backup-20260304.tar.gz

# 恢复命名卷
docker run --rm -v opencrawler_browser_data:/data -v $(pwd):/backup alpine tar -xzf /backup/browser_data.tar.gz -C /
```

---

## 网络配置

### 端口映射

| 服务 | 容器端口 | 宿主机端口 | 说明 |
|------|----------|------------|------|
| API | 8000 | 8000 | REST API |
| MCP | 8765 | 8765 | MCP Server |

### 自定义网络

```yaml
version: '3.8'

networks:
  opencrawler-net:
    driver: bridge

services:
  opencrawler-api:
    networks:
      - opencrawler-net
```

### 修改端口

```bash
# 使用其他端口
docker compose up -d -e PORT=9000

# 或修改 docker-compose.yml
ports:
  - "9000:8000"
```

### 外部访问配置

```yaml
# 允许外部访问
environment:
  - HOST=0.0.0.0

# 或绑定特定 IP
ports:
  - "192.168.1.100:8000:8000"
```

---

## 多环境配置

### 环境文件

创建不同环境的配置文件：

```bash
.env.development   # 开发环境
.env.production    # 生产环境
.env.test          # 测试环境
```

### 开发环境配置

```env
# .env.development
HOST=127.0.0.1
PORT=8000
API_TOKEN=
BROWSER_HEADLESS=true
DEBUG=true
```

### 生产环境配置

```env
# .env.production
HOST=0.0.0.0
PORT=8000
API_TOKEN=your_secure_production_token
BROWSER_HEADLESS=true
DEBUG=false
```

### 使用环境文件

```bash
# 指定环境文件
docker compose --env-file .env.production up -d

# 或使用多个 compose 文件
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 生产环境 Compose 文件

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  opencrawler-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
      restart_policy:
        condition: on-failure
        max_retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 常见问题

### 1. 容器启动失败

**症状：** 容器启动后立即退出

**排查步骤：**

```bash
# 查看容器日志
docker compose logs

# 查看容器退出码
docker compose ps

# 检查配置文件
docker compose config
```

**常见原因：**
- 端口被占用
- 权限问题
- 配置文件错误

### 2. 无法访问服务

**症状：** curl 请求超时或拒绝连接

**排查步骤：**

```bash
# 检查容器是否运行
docker compose ps

# 检查端口映射
docker port opencrawler-api

# 检查防火墙
sudo ufw status
```

**解决方案：**
- 确认容器正在运行
- 检查端口是否被占用
- 检查防火墙设置

### 3. 内存不足

**症状：** 容器被 OOM Killed

**排查步骤：**

```bash
# 查看资源使用
docker stats

# 查看容器事件
docker events
```

**解决方案：**
- 增加内存限制
- 减少并发请求
- 优化爬虫配置

### 4. 浏览器启动失败

**症状：** Playwright 相关错误

**排查步骤：**

```bash
# 进入容器检查
docker compose exec opencrawler-api bash
playwright --version
```

**解决方案：**
- 确保镜像包含浏览器
- 检查依赖库是否完整

### 5. 数据丢失

**症状：** 重启后数据丢失

**原因：** 未正确配置数据卷

**解决方案：**
- 使用绑定挂载或命名卷
- 定期备份数据

### 6. Cookie 失效

**症状：** 知乎/小红书爬取失败

**解决方案：**
- 更新 Cookie 配置
- 重启容器使配置生效

```bash
# 更新 .env 文件后重启
docker compose restart
```

### 7. 镜像拉取失败

**症状：** 无法拉取镜像

**解决方案：**
- 检查网络连接
- 使用镜像加速器
- 本地构建镜像

```bash
# 配置镜像加速器
echo '{"registry-mirrors": ["https://mirror.ccs.tencentyun.com"]}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

---

## 附录

### 常用命令速查

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f

# 进入容器
docker compose exec opencrawler-api bash

# 更新镜像
docker compose pull && docker compose up -d

# 查看状态
docker compose ps
```

### 飞牛 NAS 部署步骤

1. 打开飞牛 NAS Docker 应用
2. 拉取镜像：`ghcr.io/tabortao/opencrawler:latest`
3. 创建容器：
   - 名称：`opencrawler-api`
   - 端口：`8000:8000`
   - 存储卷：
     - `/app/output` → 本地目录
     - `/app/data` → 本地目录
   - 环境变量（可选）
4. 启动容器

### MCP 服务部署

1. 创建新容器
2. 使用相同镜像
3. 端口：`8765:8765`
4. 启动命令：`python mcp_server.py http --host 0.0.0.0 --port 8765`

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

LABEL maintainer="OpenCrawler"
LABEL description="多平台网页 Markdown 提取 API + MCP Server"
LABEL version="2.0.6"

WORKDIR /app

# 安装运行时依赖（Playwright chromium 需要的库）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 从构建阶段复制 Playwright 浏览器
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# 设置 Playwright 环境变量
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# 创建非 root 用户（安全考虑）
RUN useradd -m -u 1000 appuser

# 创建必要的目录
RUN mkdir -p /app/output /app/data && \
    chown -R appuser:appuser /app

# 复制应用代码
COPY --chown=appuser:appuser . .

# 切换到非 root 用户
USER appuser

# 暴露端口（API: 8000, MCP HTTP: 8765）
EXPOSE 8000 8765

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# 默认启动 API 服务
CMD ["python", "main.py"]

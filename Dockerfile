# 建構階段
FROM python:3.13-slim AS builder

# 安裝編譯依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 設置工作目錄
WORKDIR /build

# 複製依賴文件
COPY requirements.txt .

# 安裝依賴到指定目錄
RUN pip install --no-cache-dir --user -r requirements.txt

# 運行階段
FROM python:3.13-slim

# 安裝運行時依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 設置工作目錄
WORKDIR /app

# 複製已安裝的依賴
COPY --from=builder /root/.local /root/.local

# 確保 pip 安裝的二進制文件在 PATH 中
ENV PATH=/root/.local/bin:$PATH

# 複製應用代碼
COPY . .

# 設置環境變量
ENV PYTHONUNBUFFERED=1

# 設定入口點，使用環境變數或預設值
CMD gunicorn "app.main:create_app()" \
    --bind 0.0.0.0:${PORT:-5001} \
    --workers 2 \
    --log-level info \
    --timeout 30 \
    --graceful-timeout 30 \
    --keep-alive 5 
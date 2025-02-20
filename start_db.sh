#!/bin/bash

# 檢查 .env 文件是否存在
if [ ! -f .env ]; then
    echo "錯誤：找不到 .env 文件"
    exit 1
fi

# 載入環境變量
source .env

# 檢查 Docker 是否運行中
if ! docker info > /dev/null 2>&1; then
    echo "錯誤：Docker 未運行"
    exit 1
fi

# 停止並移除現有的容器（如果存在）
echo "停止並清理現有容器..."
docker-compose down -v

# 啟動新的容器
echo "啟動資料庫容器..."
docker-compose up -d

# 等待資料庫準備就緒
echo "等待資料庫準備就緒..."
max_retries=30
count=0
while ! docker-compose exec db pg_isready -U $POSTGRES_USER -d $POSTGRES_DB > /dev/null 2>&1; do
    sleep 1
    count=$((count + 1))
    if [ $count -eq $max_retries ]; then
        echo "錯誤：資料庫啟動超時"
        exit 1
    fi
done

echo "資料庫已準備就緒！"
echo "連接資訊："
echo "主機：localhost"
echo "端口：$POSTGRES_PORT"
echo "資料庫：$POSTGRES_DB"
echo "用戶：$POSTGRES_USER" 
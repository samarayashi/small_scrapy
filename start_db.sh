#!/bin/bash

# 解析命令行參數
REINIT=false
for arg in "$@"
do
    case $arg in
        --reinit)
        REINIT=true
        shift # 移除參數
        ;;
    esac
done

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

# 停止現有的容器
echo "停止現有容器..."
if [ "$REINIT" = true ]; then
    echo "檢測到 --reinit 參數，將完全重新初始化資料庫..."
    docker-compose down -v
else
    docker-compose down
fi

# 啟動新的容器
echo "啟動資料庫容器..."
docker-compose up -d

# 設置等待時間
max_retries=30

# 等待資料庫準備就緒
echo "等待資料庫準備就緒..."
count=0
while true; do
    if docker-compose exec db pg_isready -U $POSTGRES_USER -d $POSTGRES_DB > /dev/null 2>&1; then
        echo "資料庫連接成功！"
        break
    fi

    count=$((count + 1))
    if [ $count -eq $max_retries ]; then
        echo "錯誤：資料庫啟動超時"
        echo "請檢查 docker logs:"
        docker-compose logs db
        exit 1
    fi

    if [ $((count % 5)) -eq 0 ]; then
        echo "仍在等待資料庫就緒... (${count}/${max_retries})"
    fi
    sleep 2  # 增加等待間隔
done

echo "資料庫已準備就緒！"
echo "連接資訊："
echo "主機：localhost"
echo "端口：$POSTGRES_PORT"
echo "資料庫：$POSTGRES_DB"
echo "用戶：$POSTGRES_USER"

if [ "$REINIT" = true ]; then
    echo "資料庫已完全重新初始化"
fi 
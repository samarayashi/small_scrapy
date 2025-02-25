#!/bin/bash

# 啟動 Docker 服務
docker-compose up -d

# 等待應用啟動
sleep 5

# 啟動 ngrok
ngrok http 5001 
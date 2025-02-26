# 智慧新聞與天氣通知系統

## 目錄
- [專案概述](#專案概述)
- [系統架構](#系統架構)
- [快速開始](#快速開始)
- [使用指南](#使用指南)
- [開發指南](#開發指南)
- [技術參考](#技術參考)
- [未來規劃](#未來規劃)
- [資源鏈接](#資源鏈接)

## 專案概述

本專案整合了新聞爬蟲、天氣 API 和 LINE 通知功能，為用戶提供個性化的新聞和天氣資訊推送服務。系統自動爬取新聞內容，獲取實時天氣資訊，並通過 LINE 平台向用戶推送個人化內容。

**主要功能模組**：
- 新聞爬蟲（中央社）
- 天氣資訊（OpenWeatherMap）
- LINE 通知平台

## 系統架構

### 模組說明

```
專案結構
├── scraper/             # 爬蟲模組
│   ├── base_spider.py   # 爬蟲基礎類別
│   └── cna/             # 中央社爬蟲
├── app/
│   ├── etl/             # 資料處理模組
│   ├── models/          # 資料模型
│   └── services/        # 排程服務
├── owm_weather/         # 天氣資訊模組
└── line_broker/         # LINE 通知模組
```

### 系統流程

```
[爬蟲模組] → [ETL 流程] → [資料庫] ↔ [排程服務] → [LINE 通知]
                                       ↑
                                  [天氣資訊]
```

## 快速開始

### 環境配置

1. **複製環境變數範本**：
   ```bash
   cp .env.example .env
   ```

2. **設定必要參數**：
   ```
   # LINE API
   LINE_CHANNEL_ACCESS_TOKEN=你的LINE頻道token
   LINE_CHANNEL_SECRET=你的LINE頻道密鑰

   # OpenWeatherMap API
   OWM_API_KEY=你的OpenWeatherMap金鑰

   # 其他設定（資料庫、ngrok等）
   ```

### 啟動服務

**使用 Docker Compose**：
```bash
# 啟動所有服務
docker-compose up

# 背景啟動
docker-compose up -d

# 重新構建並啟動
docker-compose up --build
```

**個別啟動服務**：
```bash
# 僅啟動資料庫
docker-compose up db

# 僅啟動應用
docker-compose up app

# 僅啟動 ngrok 通道
docker-compose up ngrok
```

### LINE Webhook 設定

1. 進入 [LINE Developers 控制台](https://developers.line.biz/console/)
2. 設定 Webhook URL: `https://<ngrok網址>/line/webhook`
3. 啟用 Webhook 並驗證連接

## 使用指南

### 基本指令

使用 `run.py` 執行各種功能：
```bash
python run.py menu      # 進入互動式選單
python run.py news      # 執行新聞爬蟲
python run.py etl       # 執行資料處理流程
python run.py notify    # 發送通知
python run.py webhook   # 啟動 Webhook 服務
```

### Docker 容器操作

```bash
# 進入容器
docker exec -it <容器ID或名稱> /bin/bash

# 查看容器日誌
docker logs <容器ID或名稱>

# 持續查看日誌
docker logs -f <容器ID或名稱>
```

## 開發指南

### 本地開發流程

**混合式開發**（僅使用容器化資料庫）：
1. 啟動資料庫容器：
   ```bash
   docker-compose up db
   ```

2. 設定本地環境連接容器化資料庫：
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/news_db
   ```

3. 在本地環境執行應用：
   ```bash
   python run.py <命令>
   ```

### 本地測試 Webhook

使用 ngrok 暴露本地服務：
```bash
ngrok http 5001
```

## 技術參考

### Docker 多階段構建

專案使用多階段構建優化容器大小和安全性：

```dockerfile
# 第一階段：編譯依賴
FROM python:3.13-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# 第二階段：運行環境
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 wget && rm -rf /var/lib/apt/lists/*
```

**主要優勢**：
- 更小的映像體積（減少 60-80% 大小）
- 更少的安全漏洞（移除編譯工具）
- 更快的部署和啟動時間

### Docker 網絡與通信

服務間透過 Docker 內部網絡通信：
```yaml
# 範例：ngrok 服務連接到 app 服務
command: http --log=stdout app:5001
```

服務健康檢查確保啟動順序：
```yaml
healthcheck:
  test: ["CMD", "wget", "--spider", "--quiet", "http://localhost:5001/line/health"]
```

### 雲端部署（Render）

**推薦部署方式**：Git 倉庫 + Dockerfile

**部署步驟**：
1. 準備包含 Dockerfile 的代碼倉庫
2. 在 Render 建立 PostgreSQL 資料庫
3. 創建 Web 服務（選擇 Git Provider）
4. 設定環境變數
5. 將 Render 域名更新到 LINE Webhook URL

## 未來規劃

- **Render 部署優化**
  - 處理免費方案資料庫限制問題
  - 考慮合併到同一資料庫或停用其他服務
  - 可以搭配render的cron job，定期爬取新聞不一定要在app裡面自訂scheduler

- **LINE 互動功能增強**
  - 完善訊息事件處理
  - 支援用戶訂閱偏好設定

- **內容擴展**
  - 增加其他新聞來源
  - 串接 LLM 進行新聞摘要生成
  - 新增機票資訊爬蟲與推播

## 資源鏈接

- [LINE Messaging API](https://developers.line.biz/en/docs/messaging-api/)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [ngrok 文檔](https://ngrok.com/docs)
- [SQLAlchemy 文檔](https://docs.sqlalchemy.org/)
- [Docker Compose 文檔](https://docs.docker.com/compose/)
- [Render 部署文檔](https://render.com/docs)


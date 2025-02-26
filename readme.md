# 智慧新聞與天氣通知系統

這份 README 不僅是專案說明，也是開發過程中的技術筆記，以記錄專案架構、開發細節和部署知識。

## 專案概述

本專案整合了新聞爬蟲、天氣 API 和 LINE 通知功能，為用戶提供個性化的新聞和天氣資訊推送服務。

```
小型智慧通知系統
├── 新聞爬蟲 (中央社)
├── 天氣資訊 (OpenWeatherMap)
└── LINE 通知平台
```

## 1. 專案架構與功能

### 1.1 模組說明

#### 爬蟲模組 (scraper/)
- **base_spider.py**: 爬蟲基礎類別，提供共用功能如請求重試和連線管理
- **cna/**: 中央社新聞爬蟲
  - **cna_menu_scraper.py**: 爬取新聞類別並存儲至 JSON 配置
  - **cna_spider.py**: 爬取新聞內容，支援分類過濾和時間範圍
- **configs/categories.json**: 新聞類別對照表，含政治、國際、科技等類別

#### ETL 處理 (app/etl/)
- **news_pipeline.py**: 資料提取、轉換、載入管道
  - 從爬蟲提取數據 (Extract)
  - 轉換為資料庫模型 (Transform)
  - 批次儲存到資料庫 (Load)
  - 內建錯誤處理和批次處理機制

#### 資料模型 (app/models/)
- **base.py**: SQLAlchemy 基礎類
- **news.py**: 新聞資料模型
  - **NewsCategory**: 新聞類別模型
  - **NewsArticle**: 新聞文章模型，含標題、URL、內容和 LLM 相關欄位

#### 天氣資訊 (owm_weather/)
- **Weather_station.py**: 天氣站類，透過 OpenWeatherMap API 獲取資料
- **utils.py**: 工具函數，如溫度轉換 (絕對溫標轉攝氏)

#### LINE 通知 (line_broker/)
- **webhook_handler.py**: 處理 LINE 平台事件，包含健康檢查端點
- **line_notification.py**: LINE 訊息發送類
- **send_notifications.py**: 推送通知功能
- **user_data.json**: 使用者資料，包含地理位置和新聞訂閱偏好

#### 排程服務 (app/services/)
- **scheduler_service.py**: 定時任務排程，自動爬取新聞和發送通知

### 1.2 架構流程

```
[爬蟲模組] → [ETL 流程] → [資料庫] ↔ [排程服務] → [LINE 通知]
                                       ↑
                                  [天氣資訊]
```

## 2. 環境設定與啟動

### 2.1 必要參數配置

複製 .env.example 至 .env 並設定以下參數：

```
# LINE Messaging API
LINE_CHANNEL_ACCESS_TOKEN=你的LINE頻道token  # 從LINE Developers Console取得
LINE_CHANNEL_SECRET=你的LINE頻道密鑰        # 從LINE Developers Console取得

# OpenWeatherMap API
OWM_API_KEY=你的OpenWeatherMap金鑰          # 從OpenWeatherMap網站申請

# ngrok (開發環境外部訪問)
NGROK_AUTHTOKEN=你的ngrok授權令牌           # 從ngrok網站註冊取得

# 資料庫設定
POSTGRES_DB=news_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432

# 應用設定
APP_PORT=5001
```

### 2.2 啟動方式

#### 使用 Docker Compose 啟動所有服務：

基本啟動：
```bash
docker-compose up
```

重新構建並啟動（程式碼或 Dockerfile 有變更時）:
```bash
docker-compose up --build
```

背景啟動：
```bash
docker-compose up -d
```

#### 分別啟動：

```bash
# 啟動資料庫
docker-compose up db

# 啟動應用
docker-compose up app

# 啟動 ngrok 通道
docker-compose up ngrok
```

#### 停止和清理容器：

停止服務：
```bash
docker-compose down
```

停止服務並移除相關卷（會清除資料庫資料）：
```bash
docker-compose down -v
```

### 2.3 LINE Webhook 設定

1. 進入 [LINE Developers 控制台](https://developers.line.biz/console/) 設定 Webhook URL
2. Webhook URL 格式: `https://<ngrok網址>/line/webhook`
3. 啟用 Webhook 並驗證連接
4. 確保已開啟 webhook 功能及訊息回應功能

## 3. Docker 與資料庫配置

### 3.1 Docker 架構

專案使用多階段建構的 Dockerfile：

```dockerfile
# 建構階段
FROM python:3.13-slim AS builder
# 安裝編譯依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 運行階段
FROM python:3.13-slim
# 安裝運行時依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    wget \
    && rm -rf /var/lib/apt/lists/*
```

#### 多階段建構 (Multi-step Build) 技術細節

1. **工作原理**：
   - 第一階段 (builder)：安裝編譯工具和開發依賴，編譯需要的二進制文件
   - 第二階段：只複製第一階段生成的結果，不包含編譯工具
   - 使用 `COPY --from=builder` 指令從第一階段複製編譯結果
參考 [專案文件](./docker-compose.yml)
參考[docker 文件](https://docs.docker.com/build/buildkit/multi-stage/)

2. **優點**：
   - **更小的映像體積**：最終映像不包含編譯工具和原始碼，減少 60-80% 大小
   - **更少的安全漏洞**：移除不必要的編譯工具減少攻擊面
   - **更快的部署**：較小的映像可以更快地分發和啟動
   - **構建快取優化**：依賴變化少時只重建必要的部分
   - **環境隔離**：開發依賴與運行環境完全分離

3. **缺點**：
   - **撰寫複雜性**：編寫和維護多階段 Dockerfile 較為複雜
   - **調試難度**：問題排查可能需要檢查多個階段
   - **構建時間**：初次構建時間可能較長
   - **緩存管理**：需要精心設計以有效利用緩存

4. **緩存管理的挑戰與最佳實踐**：

   多階段構建中的緩存管理比單階段構建更為複雜，需要特別注意以下幾點：

   a. **緩存機制的挑戰**：
      - 每個構建階段都有獨立的緩存系統
      - 階段間的緩存依賴關係較為複雜
      - `COPY --from=builder` 指令不會自動感知源階段的變化
      - 不合理的指令順序容易導致緩存失效

   b. **常見的緩存失效問題**：
      ```dockerfile
      # 不好的做法：先複製全部程式碼
      COPY . .  
      # 依賴安裝（每次程式碼變更都會重複執行這個耗時步驟）
      RUN pip wheel --no-cache-dir --wheel-dir=/build/wheels -r requirements.txt
      ```

   c. **最佳實踐策略**：
      - **依賴分離**：先複製和安裝依賴文件，再複製應用程式碼
      ```dockerfile
      # 優先複製依賴文件
      COPY requirements.txt .
      # 先安裝依賴（只有 requirements.txt 變更才會重建）
      RUN pip wheel --no-cache-dir --wheel-dir=/build/wheels -r requirements.txt
      # 再複製其他程式碼
      COPY . .
      ```
      
      - **使用 .dockerignore**：排除不必要的文件，如 `__pycache__/`、`.git/`、`.venv/` 等
      
      - **使用 BuildKit 緩存掛載**：
      ```dockerfile
      # 使用緩存掛載加速依賴安裝
      RUN --mount=type=cache,target=/root/.cache/pip \
          pip wheel --wheel-dir=/wheels -r requirements.txt
      ```

      - **明確命名階段並處理階段間依賴**：使用清晰的階段名稱，便於維護和理解

   d. **實際影響**：
      - 未優化的緩存策略可能導致每次程式碼變更都需重新安裝所有依賴
      - 優化後可將構建時間從分鐘級縮短到秒級
      - 在 CI/CD 流水線中尤為重要，可大幅提高開發效率

多階段建構是容器化應用的最佳實踐，特別適合生產環境部署。理解並優化緩存管理可顯著提升開發效率和構建速度。

### 3.2 Docker Compose 服務配置

參考 [Docker Compose 文件](./docker-compose.yml)

### 3.3 資料庫配置

- 使用 PostgreSQL 作為資料庫
- SQLAlchemy 作為 ORM
- 資料實體關係:
  ```
  【資料實體關係圖】
  
  NewsCategory <------ NewsArticle -----> User
     (類別)        |      (文章)          (用戶)
                  |
                  v
                時間元數據
  
  • 每個新聞文章屬於一個新聞類別（多對一關係）
  • 用戶可訂閱多個新聞類別（多對多關係，通過偏好設定實現）
  • 新聞文章包含內容數據及 LLM 生成的元數據（摘要、情感等）
  • 用戶資料儲存用戶識別信息及其通知偏好設定
  ```

資料庫連接管理：
```python
# 通過 db_manager 提供統一的連接管理
from app.database.connection import db_manager

with db_manager.get_session() as session:
    # 資料庫操作
```

## 4. 技術筆記

### 4.1 Docker 網絡與服務通信

Docker Compose 會創建一個默認網絡，所有服務容器都連接到這個網絡，並可以通過服務名稱相互訪問：

```yaml
# ngrok 服務連接到 app 服務
command: http --log=stdout app:5001
```

這裡的 `app` 是服務名，Docker 內部 DNS 會自動解析為 app 容器的 IP 地址。這種服務發現機制是 Docker 網絡的核心特性，使得容器間通信變得簡單。

#### Docker 內部 DNS 解析原理
1. Docker 在創建網絡時會啟動內嵌的 DNS 服務器
2. 每個容器啟動時，Docker 會更新此 DNS 服務器
3. 容器可以使用服務名稱而非 IP 進行通信（服務名稱解析為容器 IP）
4. 即使容器重啟、IP 變更，服務名稱仍然有效

### 4.2 端口映射與內部通信

Docker Compose 中的端口映射 `${APP_PORT:-5001}:5001`：
- 左側 `${APP_PORT:-5001}`: 主機端口，可通過環境變數設定
- 右側 `5001`: 容器內部端口，固定值

重要概念：
- 容器間通信使用的是內部端口，與主機映射無關
- 環境變數僅影響主機映射端口，不影響容器間通信
- 服務名稱解析僅在 Docker 內部網絡有效

### 4.3 健康檢查

健康檢查確保服務依賴順序正確，防止服務啟動過早：

```yaml
healthcheck:
  test: ["CMD", "wget", "--spider", "--quiet", "http://localhost:5001/line/health"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 5s
```

參數解釋：
- `test`: 執行的檢查命令
- `interval`: 檢查間隔時間
- `timeout`: 命令超時時間
- `retries`: 失敗重試次數
- `start_period`: 容器啟動後的寬限期

服務依賴於健康檢查：
```yaml
depends_on:
  app:
    condition: service_healthy
```

這確保了 ngrok 服務只在 app 服務健康檢查通過後才啟動。

### 4.4 ngrok 設定與應用

ngrok 用於在開發環境中創建公開 URL，使 LINE 平台能訪問本地服務：

```yaml
command: http --log=stdout app:5001
```

啟動後可查看 ngrok 日誌獲取公開 URL：
```
ngrok-1  | t=2025-02-25T18:32:14+0000 lvl=info msg="started tunnel" obj=tunnels name=command_line addr=http://app:5001 url=https://42cf-27-242-70-107.ngrok-free.app
```

也可以在容器外通過瀏覽器訪問 `http://localhost:4040` 查看 ngrok 管理介面。

### 4.5 部署注意事項

部署到 Render 等雲服務時：
- 使用 Dockerfile 而非 docker-compose.yml
- 設置正確的環境變數
- 確保資料庫連接字串設定正確
- 若需外部訪問，確保使用服務提供的域名而非 ngrok
- 連接外部已託管的資料庫服務

#### Render 部署步驟

Render 提供三種部署選項：

1. **使用現有映像** (Existing Image)
   - 適合已將專案打包為 Docker 映像並上傳到 Docker Hub
   - 優點：部署速度快、映像已在本地測試過、適合複雜依賴環境
   - 缺點：需手動更新映像，缺乏自動化部署流程

2. **Git 倉庫整合** (Git Provider / Public Repository)
   - 直接連接 GitHub/GitLab 等代碼倉庫
   - 優點：自動 CI/CD 整合、可設置自動部署特定分支、可查看構建歷史
   - 即使專案使用 Dockerfile 也建議選擇此選項，Render 會自動檢測並使用根目錄中的 Dockerfile

3. **直接上傳源碼** (Source Code)
   - 適合簡單應用或不使用 Git 的場景
   - 缺乏版本控制，更新較為麻煩

**推薦部署方式**：Git 倉庫 + Dockerfile 組合
- 在專案根目錄放置 Dockerfile
- 選擇 "Git Provider" 部署選項連接 GitHub/GitLab
- Render 會自動檢測 Dockerfile 並構建映像
- 推送新代碼時自動重建和部署
- 既利用容器化優勢，又保持自動部署的便利性

**基本部署流程**：

1. **準備工作**
   - 確保代碼倉庫包含完整的 Dockerfile
   - 在 Render 上創建 PostgreSQL 資料庫服務

2. **創建 Web 服務**
   - 選擇適合的部署選項（推薦 Git Provider）
   - 配置服務名稱、區域和實例類型

3. **環境變數設定**
   ```
   DATABASE_URL=postgresql://postgres:password@db.internal:5432/news_db
   LINE_CHANNEL_ACCESS_TOKEN=你的LINE頻道token
   LINE_CHANNEL_SECRET=你的LINE頻道密鑰
   OWM_API_KEY=你的OpenWeatherMap金鑰
   ```

4. **部署後配置**
   - 將 Render 分配的域名更新到 LINE Developers Console 的 Webhook URL

注意：Render 免費方案的資料庫實例有限制，目前僅有一個免費實例可用。您可以考慮：
- 停用其他服務以釋放資料庫資源
- 使用同一個資料庫服務但使用不同的資料庫名稱
- 升級到付費方案以獲得更多資源

## 5. 資源與參考

- [LINE Messaging API](https://developers.line.biz/en/docs/messaging-api/)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [ngrok 文檔](https://ngrok.com/docs)
- [SQLAlchemy 文檔](https://docs.sqlalchemy.org/)
- [Docker Compose 文檔](https://docs.docker.com/compose/)
- [Render 部署文檔](https://render.com/docs)
- [Docker Hub 文檔](https://docs.docker.com/docker-hub/)

## 6. 開發與調試

### 6.1 本地開發

#### 使用 docker-compose 單獨啟動資料庫進行開發

有時我們只需要資料庫服務，而在本地開發應用程式，這種混合模式開發流程如下：

1. 啟動單獨的資料庫服務：
   ```bash
   docker-compose up db
   ```

2. 在本地開發環境中，修改環境變數連接到 Docker 中的資料庫：
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/news_db
   ```
3. 使用 run.py 進行本地開發和調試：

    ```bash
    python run.py menu
    ```

    測試新聞爬蟲：

    ```bash
    python run.py news
    ```

    執行 ETL 流程：

    ```bash
    python run.py etl
    ```

    發送通知：

    ```bash
    python run.py notify
    ```

    啟動 Webhook 服務：

    ```bash
    python run.py webhook
    ```

使用 ngrok 暴露本地服務：`ngrok http 5001`

#### Docker 容器內部調試
使用以下命令進入運行中的容器：
```bash
docker exec -it <容器ID或名稱> /bin/bash
```

查看容器日誌：
```bash
docker logs <容器ID或名稱>

# 持續查看日誌
docker logs -f <容器ID或名稱>
```

todo:
- 補上render部署
  - 現在免費方案的資料庫已經被佔用
  - 看是要合併到同一個資料庫，或是停掉其他服務後再部署
- 更完整實作line event 的處理，讓user可以在line 上訂閱天氣或新聞
  - 現在只有處理follow事件，把user id 註冊進資料庫
  - 需要處理消息事件，根據user id 發送新聞或天氣通知
  - 新聞來源中央社，需要增加其他新聞來源
  - 串接LLM 進行新聞摘要生成
- 機票爬蟲
  - 爬取機票資訊
  - 推播機票資訊


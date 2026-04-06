# 技術方案：全球航班搜尋

## 對應規格
- Spec: specs/global-flight-search/spec.md
- 狀態：`approved`

## 工作估算
- **複雜度**：L（Large）
- **預估任務數**：10
- **預估階段**：3 個 Phase

## 技術選型

| 技術 | 選擇 | 理由 |
|------|------|------|
| 機場資料 | OpenFlights + OurAirports 開源資料集 | 免費、含 IATA 代碼 + 中英文城市名、9,000+ 機場 |
| 前端機場搜尋 | 前端本地搜尋（JSON 資料載入） | < 200ms 回應，不需 API call |
| 長榮爬蟲 | httpx + BeautifulSoup / Playwright | 官網航班查詢頁面 |
| 星宇爬蟲 | httpx + BeautifulSoup / Playwright | 官網航班查詢頁面 |
| 第三方 API | Amadeus Flight Offers API（備選） | 如果爬蟲不穩定時作為補充 |
| 快取 | Redis（生產）/ In-memory dict（開發） | 同條件 30 分鐘不重複查詢 |

## 架構設計

### 系統架構

```
前端 (Web / React Native)
├── 機場搜尋器 (本地 JSON, < 200ms)
│   └── airports.json (~500KB)
├── 搜尋表單 (單程 / 來回 / 外站票 三模式)
└── 結果顯示 (時間軸卡片 + 外站票比較)
    ↓ API
後端 (FastAPI)
├── GET  /api/airports?q=tokyo     ← 機場搜尋 API（備用）
├── POST /api/flights/search       ← 單程/來回搜尋
│   ├── CrawlerRouter
│   │   ├── EvaAirCrawler (長榮)
│   │   ├── StarluxCrawler (星宇)
│   │   └── AmadeusCrawler (第三方 API, 備選)
│   ├── Redis Cache (30 min TTL)
│   └── SimulatedCrawler (fallback)
└── POST /api/tickets/search       ← 既有外站票搜尋（升級用全球機場）
```

### 元件拆解

#### 1. 全球機場資料模組
- 下載 OpenFlights/OurAirports 資料，轉換為 JSON
- 欄位：IATA code, 城市名(中/英), 國家, 機場全名, 經緯度, 時區
- 前端：載入 JSON，本地模糊搜尋（Fuse.js 或自製）
- 後端：提供 API 作為備用

#### 2. 航班搜尋 API（新）
- `POST /api/flights/search`
- 支援 `trip_type`: "one_way" | "round_trip"
- 呼叫 CrawlerRouter 分派到各航空公司爬蟲
- 合併結果、排序、回傳
- 標示每筆資料的來源（真實/模擬）

#### 3. CrawlerRouter（爬蟲路由器）
- 管理多個爬蟲，平行呼叫
- 爬蟲失敗時標記，不 crash 整個搜尋
- 結果合併 + 去重

#### 4. 長榮航空爬蟲（EvaAirCrawler）
- 爬取 evaair.com 航班查詢
- Playwright 模擬瀏覽器操作
- 解析搜尋結果：航班、時間、價格

#### 5. 星宇航空爬蟲（StarluxCrawler）
- 爬取 starlux-airlines.com 航班查詢
- 同上架構

#### 6. 來回搜尋結果 + 外站票比較
- 搜尋來回票時，同時觸發外站票搜尋
- 在結果中顯示「外站票可能更便宜」提示

### 資料模型變更

```
airports (新 JSON 檔案，非 DB table)
├─ iata_code: "TPE"
├─ name_zh: "桃園國際機場"
├─ name_en: "Taoyuan International Airport"
├─ city_zh: "台北"
├─ city_en: "Taipei"
├─ country_zh: "台灣"
├─ country_en: "Taiwan"
└─ timezone: "Asia/Taipei"

flight_results (API response, 非 DB)
├─ airline: "長榮航空"
├─ flight_number: "BR108"
├─ origin / destination
├─ departure_datetime / arrival_datetime
├─ duration_minutes
├─ price / currency
├─ source: "evaair" | "starlux" | "simulated"
├─ cached: bool
└─ stops: [{ city, wait_minutes }]
```

不需要新增 DB table — 航班搜尋結果是即時的，不需要持久化。

## 整合點
- 擴展現有 `app/tickets/` 模組，新增 `app/flights/` 模組
- 現有外站票搜尋的 `outstation.py` 升級使用全球機場資料
- 前端搜尋表單改為三模式切換（單程/來回/外站票）
- 前端機場輸入改為搜尋式選擇器

## 風險評估

| 風險 | 可能性 | 影響 | 緩解方案 |
|------|--------|------|----------|
| 航空公司官網反爬蟲 | 高 | 無法取得真實資料 | Playwright 模擬 + 合理間隔 + fallback 標示 |
| 官網改版導致爬蟲失效 | 中 | 爬蟲需要更新 | 模組化設計，爬蟲可獨立更新 |
| 全球機場 JSON 太大影響載入 | 低 | 首次載入慢 | 壓縮後 ~300KB，gzip 後 ~100KB，可接受 |
| Playwright 佔用記憶體 | 中 | 伺服器成本 | 限制同時爬取數量 + 快取減少請求 |

## 安全性考量
- 爬蟲請求間隔 ≥ 3 秒，避免被視為攻擊
- 不儲存航空公司的登入資訊
- 前端機場資料不含敏感資訊

## 實作策略

**Phase A：全球機場資料（基礎設施）**
- 下載並處理機場資料
- 後端 API + 前端搜尋器
- 升級外站票搜尋使用全球機場

**Phase B：單程/來回搜尋 + 爬蟲**
- 航班搜尋 API + CrawlerRouter
- 長榮爬蟲 + 星宇爬蟲
- SimulatedCrawler 升級

**Phase C：前端整合 + 外站票比較**
- 三模式搜尋表單（單程/來回/外站票）
- 來回搜尋結果頁面
- 外站票比較提示

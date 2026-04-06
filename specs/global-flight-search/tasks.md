# 任務清單：全球航班搜尋

## 對應規格
- Spec: specs/global-flight-search/spec.md
- Plan: specs/global-flight-search/plan.md

---

## Phase A：全球機場資料（基礎設施）

### 任務 A.1：全球機場資料集建置 [P-group-A]
- **對應 User Story**：US-12（全球機場搜尋選擇器）
- **描述**：下載 OpenFlights/OurAirports 開源資料，處理為含中英文的 JSON 格式
- **驗收條件**：
  - [ ] airports.json 包含 5,000+ IATA 認證機場
  - [ ] 每個機場包含：iata_code, name_zh, name_en, city_zh, city_en, country_zh, country_en
  - [ ] 資料去重、清洗（排除無 IATA 代碼的機場）
  - [ ] 含熱門機場標記（top 100）
- **測試策略**：單元測試 — 驗證資料格式、數量、必填欄位
- **狀態**：`todo`

### 任務 A.2：後端機場搜尋 API [P-group-A]
- **對應 User Story**：US-12
- **描述**：GET `/api/airports?q=tokyo` 模糊搜尋 API（作為前端備用）
- **驗收條件**：
  - [ ] 支援中文和英文搜尋
  - [ ] 模糊匹配：「東京」→ NRT, HND；「tokyo」→ NRT, HND
  - [ ] 回傳前 20 筆結果，熱門機場優先
  - [ ] 回應時間 < 100ms
- **測試策略**：整合測試 — API 搜尋中英文、模糊匹配
- **狀態**：`todo`

### 任務 A.3：前端機場搜尋選擇器 [depends: A.1]
- **對應 User Story**：US-12
- **描述**：前端載入 airports.json，實作帶搜尋的機場下拉選擇器（替換目前的手動輸入 + chips）
- **驗收條件**：
  - [ ] 輸入時即時搜尋（debounce 150ms）
  - [ ] 下拉顯示匹配結果：代碼 + 城市 + 國家
  - [ ] 選擇後填入機場代碼
  - [ ] 支援鍵盤導覽（↑↓ 選擇、Enter 確認）
  - [ ] 手機上觸控友善
- **測試策略**：手動測試 — 搜尋各語言、選擇流程
- **狀態**：`todo`

### 任務 A.4：升級外站票搜尋使用全球機場 [depends: A.1]
- **對應 User Story**：US-12（影響現有 US-1）
- **描述**：將 `outstation.py` 的硬編碼城市清單改為從機場資料載入，外站城市可依地區篩選
- **驗收條件**：
  - [ ] 外站城市不再硬編碼，從機場資料動態載入
  - [ ] 保留地區篩選功能（東北亞、東南亞、歐美等）
  - [ ] 既有外站票測試仍通過
- **測試策略**：單元測試 — 驗證組合數量增加、篩選功能正常
- **狀態**：`todo`

---

## Phase B：單程/來回搜尋 + 爬蟲

### 任務 B.1：航班搜尋 API + CrawlerRouter
- **對應 User Story**：US-13, US-14
- **描述**：新增 `POST /api/flights/search` API，支援 trip_type（one_way / round_trip），CrawlerRouter 分派到多個爬蟲平行搜尋
- **驗收條件**：
  - [ ] POST `/api/flights/search` 接受 origin, destination, departure_date, return_date(可選), passengers, trip_type
  - [ ] CrawlerRouter 平行呼叫所有可用爬蟲
  - [ ] 合併結果，去重，排序
  - [ ] 每筆結果標示 source（航空公司名 / simulated）
  - [ ] 快取 30 分鐘
- **測試策略**：整合測試 — API 端到端、排序、快取
- **狀態**：`todo`

### 任務 B.2：長榮航空爬蟲（EvaAirCrawler）
- **對應 User Story**：US-15
- **描述**：爬取 evaair.com 航班查詢頁面，取得航班時刻和票價
- **驗收條件**：
  - [ ] 可查詢指定日期/航線的航班
  - [ ] 解析結果：航班號、時間、價格、艙等
  - [ ] 請求間隔 ≥ 3 秒
  - [ ] 失敗時回傳 None（不 crash）
  - [ ] 標示資料來源為 "evaair"
- **測試策略**：整合測試 — 真實查詢 + mock 測試
- **狀態**：`todo`

### 任務 B.3：星宇航空爬蟲（StarluxCrawler）
- **對應 User Story**：US-15
- **描述**：爬取 starlux-airlines.com 航班查詢頁面
- **驗收條件**：
  - [ ] 同 B.2 的驗收條件
  - [ ] 標示資料來源為 "starlux"
- **測試策略**：整合測試 — 真實查詢 + mock 測試
- **狀態**：`todo`

### 任務 B.4：SimulatedCrawler 升級 [P-group-B]
- **對應 User Story**：US-13, US-14
- **描述**：升級模擬爬蟲支援單程/來回搜尋，使用全球機場資料生成更真實的模擬結果
- **驗收條件**：
  - [ ] 支援單程和來回模式
  - [ ] 模擬結果標示 source: "simulated"
  - [ ] 模擬價格根據距離合理計算
- **測試策略**：單元測試
- **狀態**：`todo`

---

## Phase C：前端整合 + 外站票比較

### 任務 C.1：三模式搜尋表單 [depends: A.3, B.1]
- **對應 User Story**：US-13, US-14, US-16
- **描述**：前端搜尋表單改為三模式切換（單程/來回/外站票），整合機場搜尋器
- **驗收條件**：
  - [ ] Tab 切換：單程 | 來回 | 外站票
  - [ ] 單程模式隱藏回程日期欄位
  - [ ] 機場輸入使用搜尋選擇器（替換手動輸入）
  - [ ] 搜尋呼叫對應的 API（flights/search 或 tickets/search）
- **測試策略**：手動測試 — 三模式切換、表單驗證
- **狀態**：`todo`

### 任務 C.2：單程/來回搜尋結果頁面 [depends: B.1]
- **對應 User Story**：US-13, US-14, US-16
- **描述**：顯示航班搜尋結果，含時間軸卡片、資料來源標示、外站票比較區塊
- **驗收條件**：
  - [ ] 結果卡片顯示：航空公司、航班號、時間、價格、資料來源標籤
  - [ ] 轉機航班展開顯示各段詳情
  - [ ] 排序切換（價格/時間/航空公司）
  - [ ] 來回模式底部顯示「外站票可能更便宜」比較區塊
  - [ ] 載入中顯示進度（因爬蟲可能需 15 秒）
  - [ ] 真實資料標 ✅、模擬資料標 ⚠️ 模擬
- **測試策略**：手動測試 + 建置驗證
- **狀態**：`todo`

---

## 進度摘要
- 總任務數：10
- 已完成：0
- 進行中：0
- 需人工介入：0

## 依賴關係

```
A.1 ──→ A.3 ──→ C.1
A.1 ──→ A.4       ↑
A.2 (平行)    B.1 ─┘──→ C.2
              B.2 (平行)
              B.3 (平行)
              B.4 (平行)
```

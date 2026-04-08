# 任務清單：旅遊規劃 App

## 對應規格
- Spec: .req/specs/travel-planner-app/spec.md
- Plan: .req/specs/travel-planner-app/plan.md

---

## Phase 1：外站票搜尋（🎯 第一優先）

### 任務 1.1：後端專案初始化
- **對應 User Story**：所有（基礎建設）
- **描述**：建立 FastAPI 後端專案結構、資料庫連線（PostgreSQL）、Redis 連線、基本 API 路由框架
- **驗收條件**：
  - [x] FastAPI 專案可啟動，`/health` 回傳 200
  - [x] PostgreSQL 連線正常（in-memory for MVP, DB model ready）
  - [x] Redis 連線正常（in-memory for MVP）
  - [x] Docker Compose 可一鍵啟動所有服務
- **狀態**：`done`

### 任務 1.2：資料模型 — 機票搜尋
- **對應 User Story**：US-1（外站票快速查找）
- **描述**：建立機票搜尋資料模型，定義 API schema
- **驗收條件**：
  - [x] Pydantic model 定義完成（FlightLeg, OutstationTicket, LayoverInfo）
  - [x] API schema（request/response）定義完成
  - [x] 增加時間軸欄位：datetime, duration, layover, total_journey_hours
- **狀態**：`done`

### 任務 1.3：外站票組合演算法
- **對應 User Story**：US-1（外站票快速查找）
- **描述**：實作外站票組合計算邏輯
- **驗收條件**：
  - [x] 輸入出發地和目的地，輸出所有可能的外站城市清單
  - [x] 每個組合正確產生四段航程
  - [x] 可設定外站城市白名單（常見轉機城市）
  - [x] 單元測試覆蓋核心邏輯（8 tests）
- **狀態**：`done`

### 任務 1.4：航空公司官網爬蟲
- **對應 User Story**：US-1（外站票快速查找）
- **描述**：實作可替換的爬蟲模組（MVP 用模擬資料）
- **驗收條件**：
  - [x] 可替換的 AirlineCrawler 介面
  - [x] SimulatedCrawler 生成含完整時間的模擬資料
  - [ ] 替換為真實航空公司官網爬蟲（待做）
- **狀態**：`done`（模擬版完成，真實爬蟲待替換）

### 任務 1.5：搜尋 API + 快取
- **對應 User Story**：US-1（外站票快速查找）
- **驗收條件**：
  - [x] POST `/api/tickets/search` 接受出發地、目的地、日期、人數
  - [x] 回傳外站票組合列表，包含四段航程、價格、時間軸、轉機等待
  - [x] 結果可依價格、轉機時間、航空公司排序
  - [x] 支援篩選器：地區
  - [x] 支援多人同行（人數 × 單價）
  - [x] 計算轉機等待時間和總旅程時間
- **狀態**：`done`

### 任務 1.6：前端專案初始化
- **對應 User Story**：所有（基礎建設）
- **驗收條件**：
  - [x] React Native (Expo) 專案建立
  - [x] 基本路由結構（Tab 導航：搜機票、紀錄、行程、記帳、個人）
  - [x] API client 設定完成
  - [x] Vite + React Web 版本建立（部署到 GitHub Pages）
- **狀態**：`done`

### 任務 1.7：外站票搜尋頁面
- **對應 User Story**：US-1（外站票快速查找）、US-2（外站票概念說明）
- **驗收條件**：
  - [x] 搜尋表單：出發地、目的地、日期、人數
  - [x] 快速機場選擇 chips
  - [x] 結果列表：時間軸卡片（每段航班日期+時間+飛行時長+轉機等待）
  - [x] 排序切換（價格/轉機時間）
  - [x] 首次使用顯示外站票概念說明 modal
  - [x] 搜尋歷史 + ⭐ 標記 + 備註
  - [x] Demo 模式（無後端時用模擬資料）
- **狀態**：`done`

---

## Phase 2：用戶驗證 + 行程規劃基礎

### 任務 2.1：用戶驗證服務
- **對應 User Story**：US-3、US-5
- **驗收條件**：
  - [x] POST `/api/auth/send-code` 發送驗證碼
  - [x] POST `/api/auth/verify` 驗證碼登入（自動註冊）
  - [x] Token middleware 保護需認證的 API
  - [x] GET/PUT `/api/auth/me` 用戶資料 CRUD
- **狀態**：`done`

### 任務 2.2：資料模型 — 旅遊計畫
- **對應 User Story**：US-3、US-4
- **驗收條件**：
  - [x] Trip, TripMember, ItineraryItem 模型完成
  - [x] 支援行程項目類型：景點、餐廳、交通、住宿、其他
  - [x] trip_members 支援角色：owner、editor、viewer
- **狀態**：`done`

### 任務 2.3：旅遊計畫 API
- **對應 User Story**：US-3、US-4
- **驗收條件**：
  - [x] POST `/api/trips` 建立計畫
  - [x] GET/PUT/DELETE `/api/trips/{id}` 管理計畫
  - [x] POST/PUT/DELETE `/api/trips/{id}/items` 管理行程項目
  - [x] PUT `/api/trips/{id}/items/reorder` 排序
  - [x] GET `/api/trips/{id}` 包含完整行程總覽
- **狀態**：`done`

### 任務 2.4：邀請與權限 API
- **對應 User Story**：US-5
- **驗收條件**：
  - [x] POST `/api/trips/{id}/invite` 產生邀請連結
  - [x] POST `/api/trips/join/{token}` 透過連結加入
  - [x] PUT `/api/trips/{id}/members/{user_id}` 設定權限
  - [x] viewer 無法編輯（權限檢查通過）
- **狀態**：`done`

### 任務 2.5：登入/註冊頁面
- **對應 User Story**：US-3、US-5
- **驗收條件**：
  - [x] 電話號碼 + 驗證碼登入頁面（React Native + Web）
  - [x] 首次登入自動註冊
  - [ ] Token 持久化（待接 SecureStore）
- **狀態**：`done`（基本完成）

### 任務 2.6：行程規劃頁面
- **對應 User Story**：US-3、US-4、US-5
- **驗收條件**：
  - [x] React Native placeholder 建立
  - [ ] 建立新計畫表單（待接 API）
  - [ ] 每日行程列表 + 拖曳排序（待做）
  - [ ] 邀請旅伴功能（待做）
- **狀態**：`in-progress`

---

## Phase 3：共同編輯與定案

### 任務 3.1：WebSocket 即時同步
- **對應 User Story**：US-7
- **驗收條件**：
  - [ ] WebSocket 連線 + 即時廣播
  - [ ] 衝突處理
  - [ ] 斷線重連
- **狀態**：`todo`（延遲到前端整合時實作）

### 任務 3.2：留言討論功能
- **對應 User Story**：US-7
- **驗收條件**：
  - [x] POST `/api/trips/{id}/items/{item_id}/comments` 新增留言
  - [x] GET 留言列表
  - [x] 編輯紀錄追蹤
- **狀態**：`done`（後端完成）

### 任務 3.3：編輯紀錄
- **對應 User Story**：US-7
- **驗收條件**：
  - [x] 每次修改記錄：修改者、時間、內容
  - [x] GET `/api/trips/{id}/history` 查看紀錄
- **狀態**：`done`（後端完成）

### 任務 3.4：定案流程
- **對應 User Story**：US-6
- **驗收條件**：
  - [x] POST `/api/trips/{id}/finalize` 發起定案（僅 owner）
  - [x] POST `/api/trips/{id}/confirm` 成員確認
  - [x] 全員確認 → 自動定案
  - [x] POST `/api/trips/{id}/unlock` 解鎖（僅 owner）
  - [x] 編輯紀錄追蹤定案/解鎖
- **狀態**：`done`（後端完成）

---

## Phase 4：記帳與拆帳

### 任務 4.1：資料模型 — 帳務
- **對應 User Story**：US-9、US-10、US-11
- **驗收條件**：
  - [x] Expense, ExpenseSplit 模型完成
  - [x] 支援多幣別
  - [x] 支援拆帳方式：均分、按比例、自訂
- **狀態**：`done`

### 任務 4.2：記帳 API
- **對應 User Story**：US-10
- **驗收條件**：
  - [x] POST `/api/trips/{id}/expenses` 快速記帳（金額 + 付款人）
  - [x] GET 花費列表
  - [x] 預設均分給所有成員
- **狀態**：`done`

### 任務 4.3：花費預估 API
- **對應 User Story**：US-9
- **驗收條件**：
  - [x] GET `/api/trips/{id}/expenses/budget` 預算摘要
  - [x] 按類別分組
  - [x] 超支偵測
- **狀態**：`done`

### 任務 4.4：拆帳結算引擎
- **對應 User Story**：US-11
- **驗收條件**：
  - [x] 均分/按比例拆帳
  - [x] 最簡化轉帳演算法（最少轉帳次數）
  - [x] GET `/api/trips/{id}/expenses/settlement` 結算報告
  - [x] PUT 標記已結清
  - [x] 單元測試覆蓋各種情境（10 tests）
- **狀態**：`done`

### 任務 4.5：記帳與拆帳頁面
- **對應 User Story**：US-9、US-10、US-11
- **驗收條件**：
  - [x] React Native placeholder 建立
  - [ ] 快速記帳 UI（待接 API）
  - [ ] 花費分佈圖（待做）
  - [ ] 拆帳結算頁面（待做）
- **狀態**：`in-progress`

---

## Phase 5：分享與匯出

### 任務 5.1：行程匯出
- **對應 User Story**：US-8
- **驗收條件**：
  - [x] GET `/api/trips/{id}/export/text` 文字版匯出
  - [x] GET `/api/trips/{id}/export/json` JSON 匯出
  - [ ] 前端圖片/PDF 匯出（待做）
- **狀態**：`done`（後端完成）

### 任務 5.2：唯讀分享連結
- **對應 User Story**：US-8
- **驗收條件**：
  - [x] GET `/api/share/{token}` 無需登入即可查看
  - [ ] Web 版唯讀行程頁面（待做）
- **狀態**：`done`（後端完成）

### 任務 5.3：結算結果分享
- **對應 User Story**：US-11
- **驗收條件**：
  - [x] GET `/api/trips/{id}/settlement/export/text` 文字版結算
  - [ ] 前端分享到 LINE/WhatsApp（待做）
- **狀態**：`done`（後端完成）

---

## 進度摘要
- 總任務數：22
- 已完成（後端+前端）：17
- 部分完成（後端 done，前端 placeholder）：4（任務 2.6, 3.1, 4.5, 5.x 前端部分）
- 待做：1（任務 3.1 WebSocket）

## 待做項目總覽

### 後端待做
- [ ] 任務 1.4：替換為真實航空公司官網爬蟲
- [ ] 任務 3.1：WebSocket 即時同步
- [ ] 後端接 PostgreSQL 持久化（目前 in-memory）

### 前端待做
- [ ] 任務 2.6：行程規劃頁面（接 API）
- [ ] 任務 4.5：記帳拆帳頁面（接 API）
- [ ] 任務 5.x：分享/匯出前端功能
- [ ] Token 持久化（SecureStore）

### 部署待做
- [ ] 後端部署到雲端（AWS/Railway/Fly.io）
- [ ] 前端連接真實後端 API
- [ ] Twilio SMS 串接

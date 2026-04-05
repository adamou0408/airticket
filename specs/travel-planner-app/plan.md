# 技術方案：旅遊規劃 App

## 對應規格
- Spec: specs/travel-planner-app/spec.md
- 狀態：`approved`

## 技術選型

| 技術 | 選擇 | 選擇理由 |
|------|------|----------|
| 前端框架 | React Native (Expo) | 一套程式碼同時支援 iOS 和 Android（spec 要求雙平台）；Expo 降低原生開發門檻 |
| 後端框架 | Python FastAPI | 高效能非同步 API、自動產生 API 文件、開發速度快 |
| 資料庫 | PostgreSQL | 關聯式資料適合行程/帳務結構、JSON 欄位支援彈性資料 |
| 即時同步 | WebSocket (FastAPI WebSocket) | 共同編輯需即時同步（spec 要求延遲 < 2 秒） |
| 機票爬蟲 | Python (httpx + BeautifulSoup/Playwright) | 從航空公司官網取得票價資料（spec 決定不用第三方 API） |
| 簡訊驗證 | Twilio SMS API | 電話號碼註冊需要簡訊驗證碼 |
| 檔案儲存 | AWS S3 / MinIO | 收據照片上傳儲存 |
| 快取 | Redis | 機票搜尋結果快取（避免重複爬取、加速回應） |
| 部署 | Docker + AWS ECS (已有 infra/) | 沿用專案既有的 Terraform/Docker 基礎設施 |

## 架構設計

### 系統架構總覽

```
┌─────────────────────────────────────────────────────┐
│                  React Native App                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ 機票搜尋  │ │ 行程規劃  │ │ 記帳拆帳  │ │ 用戶驗證│ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ │
└───────┼────────────┼────────────┼────────────┼──────┘
        │ REST API   │ WebSocket  │ REST API   │ SMS
┌───────┴────────────┴────────────┴────────────┴──────┐
│                   FastAPI Backend                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ 爬蟲引擎  │ │ 行程服務  │ │ 帳務服務  │ │ 驗證服務│ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ │
│       │            │            │            │      │
│  ┌────┴─────┐ ┌────┴─────┐ ┌───┴────┐  ┌───┴────┐ │
│  │  Redis   │ │PostgreSQL│ │  S3    │  │ Twilio │ │
│  │ (快取)   │ │ (主資料庫)│ │(檔案)  │  │ (簡訊) │ │
│  └──────────┘ └──────────┘ └────────┘  └────────┘ │
└─────────────────────────────────────────────────────┘
```

### 元件拆解

#### 1. 驗證服務 (Auth Service)
- 電話號碼 + 簡訊驗證碼登入
- JWT Token 管理
- 用戶基本資料管理

#### 2. 機票爬蟲引擎 (Ticket Crawler Engine) — 🎯 第一優先
- 從航空公司官網爬取票價
- 外站票組合演算法：給定出發地和目的地，自動計算所有可能的四段票組合
- 結果快取到 Redis（同一條件 30 分鐘內不重複爬取）
- 支援篩選器：地區、時間範圍、航空公司
- 價格排序（預設）+ 轉機時間排序

#### 3. 行程服務 (Trip Service)
- 旅遊計畫 CRUD
- 每日行程項目管理（新增、排序、修改、刪除）
- 邀請連結產生 + 權限管理
- WebSocket 即時同步（共同編輯）
- 定案流程：發起確認 → 等待所有成員確認 → 鎖定
- 行程匯出（圖片/PDF）
- 唯讀分享連結

#### 4. 帳務服務 (Expense Service)
- 花費預估（自動加總行程項目的預估花費）
- 快速記帳（金額 + 付款人，其他選填）
- 收據照片上傳
- 多幣別支援 + 匯率換算
- 拆帳計算引擎（均分/按比例/自訂）
- 最簡化轉帳方案演算法
- 結算報告產出 + 分享

### 元件互動

1. **用戶註冊/登入** → Auth Service → Twilio 發送簡訊 → 驗證 → 發 JWT
2. **搜尋外站票** → Ticket Crawler → 檢查 Redis 快取 → 無快取則爬取官網 → 回傳排序結果
3. **建立行程** → Trip Service → PostgreSQL → 產生邀請連結
4. **共同編輯** → WebSocket 連線 → Trip Service → 廣播變更給所有連線用戶
5. **記帳** → Expense Service → PostgreSQL → 即時更新預算狀況
6. **定案** → Trip Service → 通知所有成員 → 等待全員確認 → 鎖定行程

## 資料模型

### 核心表格

```
users              trips              trip_members
├─ id              ├─ id              ├─ trip_id (FK)
├─ phone           ├─ name            ├─ user_id (FK)
├─ name            ├─ destination     ├─ role (owner/editor/viewer)
└─ created_at      ├─ start_date     └─ confirmed (bool)
                   ├─ end_date
                   ├─ budget
                   ├─ status (planning/finalized)
                   ├─ owner_id (FK)
                   └─ share_token

itinerary_items    expenses           expense_splits
├─ id              ├─ id              ├─ expense_id (FK)
├─ trip_id (FK)    ├─ trip_id (FK)    ├─ user_id (FK)
├─ day_number      ├─ amount          ├─ amount
├─ order           ├─ currency        └─ settled (bool)
├─ type            ├─ category
├─ name            ├─ payer_id (FK)
├─ time            ├─ note
├─ location        ├─ receipt_url
├─ note            └─ created_at
├─ estimated_cost
└─ created_by (FK)

ticket_searches    ticket_results
├─ id              ├─ search_id (FK)
├─ origin          ├─ outstation_city
├─ destination     ├─ legs (JSON)
├─ departure_date  ├─ total_price
├─ return_date     ├─ direct_price
├─ passengers      ├─ savings
└─ cached_until    └─ transit_time
```

## 與現有系統的整合點

- 沿用 `infra/docker/` 的 Dockerfile 和 docker-compose 結構
- 沿用 `infra/terraform/` 的 AWS ECS 部署架構
- 沿用 `.github/workflows/` 的 CI/CD 和閉環回饋機制
- 後端放在 `src/backend/`，前端放在 `src/frontend/`（已有目錄結構）

## 風險評估

| 風險 | 可能性 | 影響 | 緩解方案 |
|------|--------|------|----------|
| 航空公司官網反爬蟲機制 | 高 | 無法取得票價資料 | 使用 Playwright 模擬瀏覽器 + 合理請求間隔 + 多 IP 輪換 + 快取減少請求量 |
| 外站票組合數量爆炸（排列組合太多） | 中 | 搜尋時間過長 | 限制外站城市清單為常見轉機城市 + 平行爬取 + 漸進式回傳結果 |
| WebSocket 即時同步複雜度 | 中 | 共同編輯衝突 | 使用 CRDT 或 OT 演算法處理衝突；MVP 先用 Last-Write-Wins + 衝突提示 |
| 多幣別匯率即時性 | 低 | 匯率不準確 | 使用免費匯率 API（如 exchangerate-api），每日更新一次即可 |
| Twilio 簡訊成本 | 低 | 營運成本 | 暫不商業化，初期用量小；可考慮加入 rate limit |

## 實作策略

### 階段劃分

**Phase 1：外站票搜尋（🎯 第一優先）**
- 後端 API + 爬蟲引擎
- 前端搜尋頁面 + 結果顯示
- 這是使用者最想看到的功能，先交付價值

**Phase 2：行程規劃基礎**
- 用戶驗證（電話號碼）
- 建立旅遊計畫 + 每日行程
- 邀請旅伴

**Phase 3：共同編輯與定案**
- WebSocket 即時同步
- 留言討論
- 全員確認定案流程

**Phase 4：記帳與拆帳**
- 快速記帳
- 拆帳計算
- 結算報告

**Phase 5：分享與匯出**
- 行程匯出（圖片/PDF）
- 唯讀分享連結
- 花費預估視覺化

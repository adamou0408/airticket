# 技術方案：核心體驗增強

## 對應規格
- Spec: specs/core-experience-enhancement/spec.md
- 狀態：`approved`

## 工作估算
- **複雜度**：L（Large）
- **預估任務數**：8
- **預估階段**：4 個 Phase

## 技術選型

| 技術 | 選擇 | 理由 |
|------|------|------|
| 前端框架 | 繼續用 Vite + React（Web 版） | 與現有 GitHub Pages 一致 |
| API 呼叫 | fetch + 統一錯誤處理 | 移除 mock 後需要完善的錯誤處理 |
| 狀態管理 | React state + localStorage | 輕量，不需要 Redux |
| 票價歷史 | 新 DB table: price_history | 記錄每次爬取的最低價 |

## 架構設計

### 變更範圍

```
前端 (src/web/)
├── 移除：mock.ts 的所有 fallback 引用
├── 新增：錯誤處理 UI 元件（ErrorMessage + RetryButton）
├── 新增：行程規劃頁面（TripsTab）
├── 新增：記帳拆帳頁面（ExpensesTab）
├── 新增：航班卡片「+ 加入行程」按鈕
├── 修改：追蹤頁面加入目標價格設定
└── 修改：搜尋結果加入「歷史新低」標籤

後端 (src/backend/)
├── 移除：SimulatedCrawler 從 CrawlerRouter
├── 新增：price_history table（記錄歷史最低價）
├── 修改：crawl_schedules 加 target_price 欄位
├── 新增：每日爬取後比對目標價格
└── 修改：搜尋 API 回傳是否為歷史新低
```

### 資料模型變更

```sql
-- 新增
ALTER TABLE crawl_schedules ADD COLUMN target_price FLOAT;
ALTER TABLE crawl_schedules ADD COLUMN alert_triggered BOOLEAN DEFAULT FALSE;

-- 新表
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    lowest_price FLOAT NOT NULL,
    source TEXT,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 風險評估

| 風險 | 可能性 | 影響 | 緩解 |
|------|--------|------|------|
| 移除 mock 後真實爬蟲全失敗 | 高 | 空結果 | 清楚錯誤訊息 + 重試按鈕 + 提示加入追蹤 |
| 行程前端 UI 複雜度高 | 中 | 開發時間長 | 先做核心 CRUD，進階功能後續迭代 |
| Render 免費方案記憶體不夠跑 Playwright | 中 | 爬蟲失敗 | 提示使用者設定追蹤讓排程爬取 |

## 實作策略

**Phase E：移除 mock（清理基礎）**
- 後端移除 SimulatedCrawler
- 前端移除所有 mock fallback
- 新增統一錯誤處理 UI

**Phase F：行程規劃 + 記帳前端**
- 行程列表 + 建立 + 詳情 + 項目 CRUD + 邀請 + 定案
- 記帳 + 預算 + 拆帳結算

**Phase G：機票 → 行程整合**
- 航班卡片「加入行程」按鈕
- 選擇計畫彈窗
- 自動建立行程項目

**Phase H：票價監控與提醒**
- 目標價格設定
- 歷史最低價追蹤
- 提醒標記

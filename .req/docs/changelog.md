# 需求變更紀錄

所有需求的狀態變更和內容更新都會記錄在這裡。

---

## 格式說明

每筆紀錄包含：
- **日期**：變更發生的日期
- **類型**：新增 / 更新 / 狀態變更 / 衝突 / 解決
- **目標**：受影響的檔案或功能
- **說明**：變更的簡要描述

---

## 紀錄

### 2026-04-05
- **新增** | `.req/intake/raw/2026-04-05-travel-planner-app.md` | 提交旅遊規劃 App 原始需求
- **新增** | `.req/personas/trip-organizer.md` | 建立「旅遊發起人」角色
- **新增** | `.req/personas/trip-member.md` | 建立「旅伴/團員」角色
- **新增** | `.req/personas/expense-manager.md` | 建立「記帳管理者」角色
- **新增** | `.req/personas/ticket-searcher.md` | 建立「機票搜尋者」角色
- **新增** | `.req/specs/travel-planner-app/spec.md` | AI 轉譯完成，狀態：`draft`，包含 11 個 User Stories
- **衝突** | `.req/conflicts/CONFLICT-001.md` | 偵測到衝突：外站票價格 vs 舒適度
- **衝突** | `.req/conflicts/CONFLICT-002.md` | 偵測到衝突：快速定案 vs 充分討論
- **衝突** | `.req/conflicts/CONFLICT-003.md` | 偵測到衝突：精確記帳 vs 使用便利性
- **解決** | `.req/conflicts/CONFLICT-001.md` | 選擇方案 1：外站票價格優先排序
- **解決** | `.req/conflicts/CONFLICT-002.md` | 選擇方案 2：充分討論，需所有成員確認才能定案
- **解決** | `.req/conflicts/CONFLICT-003.md` | 選擇方案 2：使用便利性優先，最簡記帳模式
- **更新** | `.req/specs/travel-planner-app/spec.md` | 回答開放問題：機票來源為官網、用戶以電話號碼註冊
- **更新** | `.req/specs/travel-planner-app/spec.md` | 回答剩餘開放問題：暫不商業化、不串接支付、不支援離線、搜尋用篩選器
- **狀態變更** | `.req/specs/travel-planner-app/spec.md` | `in-review` → `approved`（人類審核通過）
- **新增** | `.req/reviews/REVIEW-travel-planner-app-2026-04-05.md` | 審核通過，所有 21 項檢查全部通過
- **狀態變更** | `.req/specs/travel-planner-app/spec.md` | `approved` → `in-progress`（開始實作）
- **實作** | Phase 1 | 外站票搜尋後端 — 爬蟲引擎、組合演算法、搜尋 API（21 tests）
- **實作** | Phase 2 | 用戶驗證 + 行程規劃 + 邀請權限（14 tests）
- **實作** | Phase 3 | 留言討論 + 編輯紀錄 + 定案流程（8 tests）
- **實作** | Phase 4 | 記帳 + 拆帳結算引擎（10 tests）
- **實作** | Phase 5 | 行程匯出 + 分享連結 + 結算分享（8 tests）
- **狀態變更** | `.req/specs/travel-planner-app/spec.md` | `in-progress` → `done`（全部後端實作完成，61 tests 通過）

### 2026-04-06
- **新增** | `.req/intake/raw/2026-04-06-airline-search-and-global-airports.md` | 新需求：單程/來回搜尋 + 全球機場 + 真實資料
- **新增** | `.req/specs/global-flight-search/spec.md` | AI 轉譯完成，狀態：`draft`，5 個 User Stories（US-12~16）
- **衝突** | `.req/conflicts/CONFLICT-004.md` | 偵測到衝突：真實資料可靠性 vs 爬蟲穩定性
- **解決** | `.req/conflicts/CONFLICT-004.md` | 方案 1：只用爬蟲，真實資料優先（長榮+星宇）
- **狀態變更** | `.req/specs/global-flight-search/spec.md` | `in-review` → `approved`（18 項審核全部通過）
- **新增** | `.req/reviews/REVIEW-global-flight-search-2026-04-06.md` | 審核通過
- **新增** | `.req/intake/raw/2026-04-06-core-experience-enhancement.md` | 核心體驗補強需求
- **新增** | `.req/specs/core-experience-enhancement/spec.md` | AI 轉譯完成，狀態：`draft`，5 個 User Stories（US-17~21）
- **衝突** | `.req/conflicts/CONFLICT-005.md` | 偵測到衝突：移除 mock 後空結果 vs 使用者體驗

### 2026-04-07
- **升級** | `req framework` | 從 flat-copy mode 升級到 submodule mode (v2.0.0 → v2.3.0)
- **新增** | `.req-framework/` | 以 git submodule 方式追蹤框架版本
- **新增** | `.req.config.yml` | 框架設定檔
- **搬移** | 業務資料 | `intake/`, `specs/`, `personas/`, `conflicts/`, `reviews/`, `docs/changelog.md` → `.req/`
- **更新** | `.claude/commands/` | 指令加上 `req-` 前綴（`/intake` → `/req-intake`）
- **新增** | `.claude/agents/req-*` | 3 個 subagent（conflict-detector, onboarder, research）
- **更新** | 所有業務資料的路徑引用 | `specs/` → `.req/specs/` 等
- **實作** | 任務 3.1 WebSocket 即時同步 | US-7 共同編輯行程完成
  - 後端：`ConnectionManager` + 5 種廣播事件（item add/update/delete、comment、finalize）
  - 前端：TripsTab 自動連線、presence 顯示、活動提示橫幅
  - 8 個測試通過，總測試數 84 → 92

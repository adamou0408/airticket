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
- **新增** | `intake/raw/2026-04-05-travel-planner-app.md` | 提交旅遊規劃 App 原始需求
- **新增** | `personas/trip-organizer.md` | 建立「旅遊發起人」角色
- **新增** | `personas/trip-member.md` | 建立「旅伴/團員」角色
- **新增** | `personas/expense-manager.md` | 建立「記帳管理者」角色
- **新增** | `personas/ticket-searcher.md` | 建立「機票搜尋者」角色
- **新增** | `specs/travel-planner-app/spec.md` | AI 轉譯完成，狀態：`draft`，包含 11 個 User Stories
- **衝突** | `conflicts/CONFLICT-001.md` | 偵測到衝突：外站票價格 vs 舒適度
- **衝突** | `conflicts/CONFLICT-002.md` | 偵測到衝突：快速定案 vs 充分討論
- **衝突** | `conflicts/CONFLICT-003.md` | 偵測到衝突：精確記帳 vs 使用便利性
- **解決** | `conflicts/CONFLICT-001.md` | 選擇方案 1：外站票價格優先排序
- **解決** | `conflicts/CONFLICT-002.md` | 選擇方案 2：充分討論，需所有成員確認才能定案
- **解決** | `conflicts/CONFLICT-003.md` | 選擇方案 2：使用便利性優先，最簡記帳模式
- **更新** | `specs/travel-planner-app/spec.md` | 回答開放問題：機票來源為官網、用戶以電話號碼註冊
- **更新** | `specs/travel-planner-app/spec.md` | 回答剩餘開放問題：暫不商業化、不串接支付、不支援離線、搜尋用篩選器

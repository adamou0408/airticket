# Coolify + Cloudflare Tunnel 部署指南

## 架構總覽

```
使用者 (HTTPS)
    ↓
Cloudflare（DNS + CDN + SSL + DDoS 防護）
    ↓ Cloudflare Tunnel（加密通道，不需開 port）
CM5 / 伺服器
├── cloudflared（Tunnel 客戶端）
├── Coolify（容器管理平台）
│   ├── Traefik（反向代理）
│   ├── App 容器（FastAPI、前端...）
│   └── PostgreSQL / Redis
```

### 為什麼選這個架構？

| 優勢 | 說明 |
|------|------|
| 不需要固定 IP | Cloudflare Tunnel 走反向連線 |
| 不需要開 port | 路由器完全不用動 |
| 自動 HTTPS | Cloudflare 免費 SSL 憑證 |
| 家中 IP 隱藏 | 使用者看不到你的真實 IP |
| 維運成本 ≈ $0 | Cloudflare 免費 + Coolify 開源 |

---

## 前置條件

| 項目 | 說明 | 費用 |
|------|------|------|
| Cloudflare 帳號 | cloudflare.com 註冊 | 免費 |
| 域名 | 例如 `yourdomain.com`，DNS 託管到 Cloudflare | ~$10/年 |
| CM5 或任何 Linux 主機 | 已安裝 Ubuntu + Docker + Coolify | 硬體成本 |
| 家用網路 | 上傳頻寬 ≥ 10 Mbps，穩定不常斷線 | 現有網路 |

---

## Step 1：安裝 cloudflared

### ARM64（Raspberry Pi CM5）

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
cloudflared --version
```

### x86_64

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
```

---

## Step 2：登入 Cloudflare

```bash
cloudflared tunnel login
```

- 會印出一個 URL，用瀏覽器開啟
- 選擇你的域名並授權
- 成功後在 `~/.cloudflared/` 產生憑證檔（`cert.pem`）

---

## Step 3：建立 Tunnel

```bash
# 建立 tunnel（取名 coolify-tunnel）
cloudflared tunnel create coolify-tunnel
```

會輸出：
```
Created tunnel coolify-tunnel with id a1b2c3d4-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

記下這個 **Tunnel ID**，並確認 credentials 檔案存在：
```bash
ls ~/.cloudflared/
# 應該有：cert.pem  a1b2c3d4-xxxx.json
```

---

## Step 4：設定 Tunnel 路由

建立設定檔：

```bash
nano ~/.cloudflared/config.yml
```

### 方案 A：直接路由（簡單，適合少數服務）

```yaml
tunnel: coolify-tunnel
credentials-file: /home/你的用戶名/.cloudflared/a1b2c3d4-xxxx.json

ingress:
  # Coolify 管理介面
  - hostname: coolify.yourdomain.com
    service: http://localhost:8000

  # AirTicket 後端 API
  - hostname: api.yourdomain.com
    service: http://localhost:3000

  # AirTicket 前端
  - hostname: airticket.yourdomain.com
    service: http://localhost:3001

  # 必須：catch-all 放最後
  - service: http_status:404
```

### 方案 B：透過 Coolify Traefik（推薦，擴展性好）

```yaml
tunnel: coolify-tunnel
credentials-file: /home/你的用戶名/.cloudflared/a1b2c3d4-xxxx.json

ingress:
  # Coolify 管理介面（直連，不經過 Traefik）
  - hostname: coolify.yourdomain.com
    service: http://localhost:8000

  # 所有其他子域名 → Coolify 的 Traefik 代理
  - hostname: "*.yourdomain.com"
    service: http://localhost:80

  # catch-all
  - service: http_status:404
```

> **方案 B 的好處**：在 Coolify 中新增 App 時，只要設定好子域名（如 `newapp.yourdomain.com`），不用修改 Tunnel config。

---

## Step 5：設定 DNS 記錄

```bash
# 為每個 hostname 建立 CNAME 記錄指向 Tunnel
cloudflared tunnel route dns coolify-tunnel coolify.yourdomain.com
cloudflared tunnel route dns coolify-tunnel api.yourdomain.com
cloudflared tunnel route dns coolify-tunnel airticket.yourdomain.com

# 如果用方案 B（wildcard），設定一條就好：
cloudflared tunnel route dns coolify-tunnel "*.yourdomain.com"
```

也可以在 Cloudflare Dashboard 手動新增：
- Type: `CNAME`
- Name: `coolify`（或 `*`）
- Target: `a1b2c3d4-xxxx.cfargotunnel.com`
- Proxy: ✅（橘色雲朵）

---

## Step 6：啟動 Tunnel

### 測試（前台運行，看 log）

```bash
cloudflared tunnel run coolify-tunnel
```

### 設為系統服務（開機自動啟動）

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# 確認狀態
sudo systemctl status cloudflared
```

### 驗證

```
https://coolify.yourdomain.com  → Coolify 管理介面
https://api.yourdomain.com/health → {"status": "ok"}
```

---

## 安全性設定（重要！）

### 1. 保護 Coolify 管理介面（Cloudflare Zero Trust）

Coolify 後台暴露在公網上很危險，務必加保護：

```
Cloudflare Dashboard
→ Zero Trust
→ Access
→ Applications
→ Add an Application

設定：
- Application name: Coolify Admin
- Application domain: coolify.yourdomain.com
- Session duration: 24 hours

Policy:
- Policy name: Only Me
- Action: Allow
- Include: Emails — 你的 email

免費方案支援最多 50 個用戶。
```

設定後，訪問 `coolify.yourdomain.com` 前會先要求 Cloudflare email 驗證。

### 2. Credentials 檔案安全

```bash
# 確保只有你能讀取
chmod 600 ~/.cloudflared/*.json
chmod 600 ~/.cloudflared/cert.pem

# 絕對不要 commit 到 git
echo ".cloudflared/" >> ~/.gitignore
```

### 3. Coolify 內建 SSL

```
Coolify 設定 → Settings → SSL
→ 關閉 Coolify 的自動 SSL

原因：Cloudflare 已經處理 SSL，
Coolify 再加一層會衝突（double encryption）。
```

---

## 注意事項

### 網路

| 情境 | 影響 | 處理 |
|------|------|------|
| 家裡斷網 | 所有服務離線 | cloudflared 重新連網後自動重連 |
| 路由器重開 | 只要 CM5 能上網就好 | 不需要任何路由器設定 |
| ISP 換 IP | 完全無影響 | Tunnel 不依賴你的 IP |
| 電腦重開 | cloudflared 系統服務自動啟動 | 確認 `systemctl enable` 有設 |

### Cloudflare 免費方案限制

| 限制 | 額度 | 影響 |
|------|------|------|
| 單一請求大小 | 100 MB | 上傳收據照片沒問題 |
| WebSocket | ✅ 支援 | 共同編輯功能可用 |
| Tunnel 數量 | 無限制 | 可建多個 |
| 頻寬 | 無限制（合理使用） | 個人專案沒問題 |
| Zero Trust 用戶 | 50 人 | 足夠 |

### Coolify 內服務的 Port 對應

```
Coolify 管理介面  → :8000（固定）
Coolify Traefik   → :80, :443（固定）
你的 App          → :3000, :3001...（Coolify 自動分配）
PostgreSQL        → :5432（內部，不對外）
Redis             → :6379（內部，不對外）
```

---

## 常用指令

```bash
# 查看 Tunnel 狀態
cloudflared tunnel info coolify-tunnel

# 查看 Tunnel 列表
cloudflared tunnel list

# 查看服務 log
sudo journalctl -u cloudflared -f

# 重啟 Tunnel
sudo systemctl restart cloudflared

# 刪除 Tunnel（小心！）
cloudflared tunnel delete coolify-tunnel
```

---

## Troubleshooting

### 連不上

1. 確認 cloudflared 正在運行：`sudo systemctl status cloudflared`
2. 看 log：`sudo journalctl -u cloudflared --since "5 min ago"`
3. 確認 DNS 記錄正確：`dig coolify.yourdomain.com`
4. 確認 Coolify 正在運行：`curl http://localhost:8000`

### SSL 錯誤

- Cloudflare Dashboard → SSL/TLS → 設定為 **Flexible** 或 **Full**
- 不要用 Full (Strict)，因為 Coolify 內部用 HTTP

### 502 Bad Gateway

- 目標服務沒在跑：`curl http://localhost:3000`
- Port 寫錯：檢查 config.yml 的 port 是否對應 Coolify 分配的 port

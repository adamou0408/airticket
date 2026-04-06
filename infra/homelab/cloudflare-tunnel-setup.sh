#!/usr/bin/env bash
# ──────────────────────────────────────────────
# Cloudflare Tunnel 設定腳本
# ──────────────────────────────────────────────
# 前提：
# - 已安裝 Coolify
# - 已有 Cloudflare 帳號
# - 域名已託管到 Cloudflare
#
# 使用方式：
#   chmod +x cloudflare-tunnel-setup.sh && ./cloudflare-tunnel-setup.sh
#
# ⚠️ 這個腳本需要互動操作（瀏覽器授權）
# ──────────────────────────────────────────────

set -euo pipefail

TUNNEL_NAME="${1:-coolify-tunnel}"
DOMAIN="${2:-}"

echo "=========================================="
echo "  Cloudflare Tunnel 設定"
echo "=========================================="

# ── 1. 安裝 cloudflared ──────────────────
echo "📥 安裝 cloudflared..."
ARCH=$(dpkg --print-architecture)
if [ "$ARCH" = "arm64" ]; then
    URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb"
else
    URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb"
fi

curl -L "$URL" -o /tmp/cloudflared.deb
sudo dpkg -i /tmp/cloudflared.deb
rm /tmp/cloudflared.deb

echo "✅ cloudflared $(cloudflared --version) 已安裝"

# ── 2. 登入 Cloudflare ──────────────────
echo ""
echo "🔐 登入 Cloudflare..."
echo "   會開啟一個 URL，請在瀏覽器中授權。"
echo ""
cloudflared tunnel login

# ── 3. 建立 Tunnel ──────────────────────
echo ""
echo "🚇 建立 Tunnel: $TUNNEL_NAME ..."
cloudflared tunnel create "$TUNNEL_NAME"

# 取得 Tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
echo "✅ Tunnel ID: $TUNNEL_ID"

# 找到 credentials 檔案
CRED_FILE="$HOME/.cloudflared/${TUNNEL_ID}.json"
echo "✅ Credentials: $CRED_FILE"

# ── 4. 產生設定檔 ────────────────────────
CONFIG_FILE="$HOME/.cloudflared/config.yml"
echo ""
echo "📝 產生設定檔: $CONFIG_FILE"

if [ -z "$DOMAIN" ]; then
    echo ""
    read -p "請輸入你的域名（例如 yourdomain.com）: " DOMAIN
fi

cat > "$CONFIG_FILE" << EOF
# Cloudflare Tunnel 設定
# 產生時間: $(date)
# Tunnel: $TUNNEL_NAME ($TUNNEL_ID)

tunnel: $TUNNEL_NAME
credentials-file: $CRED_FILE

ingress:
  # Coolify 管理介面
  - hostname: coolify.$DOMAIN
    service: http://localhost:8000

  # 所有其他子域名 → Coolify Traefik 代理
  - hostname: "*.$DOMAIN"
    service: http://localhost:80

  # catch-all（必須放最後）
  - service: http_status:404
EOF

echo "✅ 設定檔已產生"
cat "$CONFIG_FILE"

# ── 5. 設定 DNS ─────────────────────────
echo ""
echo "🌐 設定 DNS 記錄..."
cloudflared tunnel route dns "$TUNNEL_NAME" "coolify.$DOMAIN"
cloudflared tunnel route dns "$TUNNEL_NAME" "*.$DOMAIN"
echo "✅ DNS 記錄已建立"

# ── 6. 測試 ─────────────────────────────
echo ""
echo "🧪 測試 Tunnel（Ctrl+C 停止）..."
echo "   請在另一個終端或瀏覽器開啟："
echo "   https://coolify.$DOMAIN"
echo ""
read -p "按 Enter 開始測試，或 Ctrl+C 跳過..."
cloudflared tunnel run "$TUNNEL_NAME" &
TUNNEL_PID=$!
sleep 5

echo ""
echo "✅ Tunnel 正在運行 (PID: $TUNNEL_PID)"
echo ""
read -p "確認可以連上後，按 Enter 設為系統服務..."
kill $TUNNEL_PID 2>/dev/null || true

# ── 7. 設為系統服務 ──────────────────────
echo ""
echo "🔧 設為系統服務（開機自動啟動）..."
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

echo ""
echo "=========================================="
echo "  ✅ Cloudflare Tunnel 設定完成！"
echo ""
echo "  Tunnel: $TUNNEL_NAME"
echo "  Tunnel ID: $TUNNEL_ID"
echo "  域名: $DOMAIN"
echo ""
echo "  可用的 URL："
echo "    https://coolify.$DOMAIN — Coolify 管理介面"
echo "    https://*.$DOMAIN — Coolify 管理的 App"
echo ""
echo "  ⚠️ 安全提醒："
echo "  1. 到 Cloudflare Zero Trust 設定 Access Policy"
echo "     保護 coolify.$DOMAIN（只允許你的 email）"
echo "  2. 確認 credentials 檔案權限："
echo "     chmod 600 $CRED_FILE"
echo ""
echo "  常用指令："
echo "    sudo systemctl status cloudflared  — 查看狀態"
echo "    sudo journalctl -u cloudflared -f  — 查看 log"
echo "    sudo systemctl restart cloudflared — 重啟"
echo "=========================================="

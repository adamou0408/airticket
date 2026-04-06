#!/usr/bin/env bash
# ──────────────────────────────────────────────
# Raspberry Pi CM5 — OS 初始化腳本
# ──────────────────────────────────────────────
# 使用方式：
#   scp os-setup.sh user@cm5-host:~/
#   ssh user@cm5-host
#   chmod +x os-setup.sh && sudo ./os-setup.sh
#
# 前提：已用 Raspberry Pi Imager 燒錄 Ubuntu Server 24.04 LTS (ARM64)
# ──────────────────────────────────────────────

set -euo pipefail

echo "=========================================="
echo "  CM5 初始化腳本"
echo "=========================================="

# ── 1. 系統更新 ──────────────────────────
echo "📦 更新系統..."
apt-get update && apt-get upgrade -y

# ── 2. 基本工具 ──────────────────────────
echo "🔧 安裝基本工具..."
apt-get install -y \
    curl wget git htop nano \
    ca-certificates gnupg lsb-release \
    unattended-upgrades

# ── 3. 設定時區 ──────────────────────────
echo "🕐 設定時區為 Asia/Taipei..."
timedatectl set-timezone Asia/Taipei

# ── 4. 安裝 Docker ───────────────────────
echo "🐳 安裝 Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    # 讓非 root 用戶也能用 docker
    usermod -aG docker "${SUDO_USER:-$USER}"
    echo "Docker 安裝完成。請重新登入讓群組生效。"
else
    echo "Docker 已安裝，跳過。"
fi

# ── 5. 安裝 Docker Compose ───────────────
echo "🐳 確認 Docker Compose..."
docker compose version || {
    echo "安裝 Docker Compose plugin..."
    apt-get install -y docker-compose-plugin
}

# ── 6. 設定 swap（CM5 4GB 建議加 swap）──
echo "💾 設定 swap..."
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "4GB swap 已建立"
else
    echo "Swap 已存在，跳過。"
fi

# ── 7. 防火牆基本設定 ────────────────────
echo "🔥 設定防火牆..."
if command -v ufw &> /dev/null; then
    ufw allow ssh
    ufw --force enable
    echo "UFW 已啟用，僅開放 SSH。"
    echo "（Cloudflare Tunnel 不需要開其他 port）"
fi

# ── 8. 自動安全更新 ──────────────────────
echo "🔄 啟用自動安全更新..."
dpkg-reconfigure -plow unattended-upgrades 2>/dev/null || true

echo ""
echo "=========================================="
echo "  ✅ 初始化完成！"
echo ""
echo "  下一步："
echo "  1. 重新登入（讓 docker 群組生效）"
echo "  2. 執行 coolify-install.sh 安裝 Coolify"
echo "  3. 執行 cloudflare-tunnel-setup.sh 設定 Tunnel"
echo "=========================================="

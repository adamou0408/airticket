#!/usr/bin/env bash
# ──────────────────────────────────────────────
# Coolify 安裝腳本
# ──────────────────────────────────────────────
# 前提：已執行 os-setup.sh（Docker 已安裝）
#
# 使用方式：
#   chmod +x coolify-install.sh && sudo ./coolify-install.sh
# ──────────────────────────────────────────────

set -euo pipefail

echo "=========================================="
echo "  安裝 Coolify"
echo "=========================================="

# ── 1. 安裝 Coolify ──────────────────────
echo "🚀 安裝 Coolify..."
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | sudo bash

echo ""
echo "=========================================="
echo "  ✅ Coolify 安裝完成！"
echo ""
echo "  管理介面：http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "  ⚠️ 重要設定："
echo "  1. 首次開啟會要求建立管理員帳號"
echo "  2. Settings → SSL → 關閉自動 SSL（讓 Cloudflare 處理）"
echo "  3. 用 Cloudflare Zero Trust 保護管理介面"
echo ""
echo "  下一步："
echo "  執行 cloudflare-tunnel-setup.sh 設定 Tunnel"
echo "=========================================="

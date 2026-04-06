# Homelab 叢集建置指南 — Super6C + Raspberry Pi CM5

## 硬體規劃

```
Super6C 主板（6 槽位）
├── Slot 1: CM5 — Coolify Master（管理節點）
├── Slot 2: CM5 — Worker 1（應用服務）
├── Slot 3: CM5 — Worker 2（資料庫）
├── Slot 4: CM5 — Worker 3（爬蟲 + 排程）
├── Slot 5: CM5 — Worker 4（備用/擴展）
└── Slot 6: CM5 — Worker 5（備用/擴展）

外部 5 台 CM5（獨立機殼）
├── CM5-6: 開發/測試環境
├── CM5-7 ~ CM5-10: 其他專案或擴展
```

## 建置步驟（TODO：硬體到貨後補充）

### Phase 1：單節點（先讓服務跑起來）
- [ ] CM5 安裝 Ubuntu Server 24.04 LTS (ARM64)
- [ ] 安裝 Docker
- [ ] 安裝 Coolify
- [ ] 安裝 cloudflared + 設定 Tunnel
- [ ] 部署 AirTicket

### Phase 2：叢集（多節點協作）
- [ ] Super6C 組裝 + 所有 CM5 安裝 OS
- [ ] 設定內部網路（靜態 IP 或 DHCP 保留）
- [ ] Coolify 新增 Worker 節點
- [ ] 服務分散到不同節點
- [ ] 設定備援 / 高可用

### Phase 3：監控 + 自動化
- [ ] Prometheus + Grafana 監控
- [ ] 閉環回饋（監控告警 → intake）
- [ ] 自動備份策略

## 硬體採購清單（TODO）

| 項目 | 數量 | 規格 | 預估價格 |
|------|------|------|---------|
| Super6C 主板 | 1 | DeskPi Super6C | 待查 |
| Raspberry Pi CM5 | 5~10 | 8GB RAM 版本 | 待查 |
| NVMe SSD | 每片 1 個 | 256GB+ | 待查 |
| 散熱器 | 每片 1 個 | | 待查 |
| 電源供應器 | 1 | 12V/5A+ | 待查 |
| 網路線 | 若干 | Cat6 | 待查 |

## 網路架構

```
家用路由器（不需要任何設定）
    ↓ 有線
Super6C 內部 Switch
    ├── CM5-1 (192.168.x.10) — Coolify Master
    ├── CM5-2 (192.168.x.11) — Worker
    ├── CM5-3 (192.168.x.12) — Worker
    ├── CM5-4 (192.168.x.13) — Worker
    ├── CM5-5 (192.168.x.14) — Worker
    └── CM5-6 (192.168.x.15) — Worker
    ↓
cloudflared Tunnel → Cloudflare → 使用者
```

> 詳細的 Cloudflare Tunnel 設定請參考 `infra/coolify/README.md`

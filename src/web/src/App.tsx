import { useState, useEffect } from 'react'
import { mockSearch, type OutstationTicket, type SearchResult } from './mock'

// ─── Styles ─────────────────────────────────────────
const CSS = `
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; background: #FAFAFA; color: #1A1A2E; -webkit-font-smoothing: antialiased; }
.app { max-width: 480px; margin: 0 auto; min-height: 100vh; background: #fff; }
.header { background: linear-gradient(135deg, #FF6B35 0%, #D4562A 100%); color: #fff; padding: 20px 20px 16px; }
.header h1 { font-size: 22px; font-weight: 700; }
.header p { font-size: 13px; opacity: 0.9; margin-top: 4px; }
.tabs { display: flex; border-bottom: 2px solid #f0f0f0; background: #fff; position: sticky; top: 0; z-index: 10; }
.tab { flex: 1; padding: 12px 8px; text-align: center; font-size: 13px; font-weight: 600; color: #9CA3AF; border: none; background: none; cursor: pointer; border-bottom: 3px solid transparent; }
.tab.active { color: #FF6B35; border-bottom-color: #FF6B35; }
.content { padding: 16px; }
.card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); border: 1px solid #f0f0f0; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 13px; font-weight: 600; color: #1A1A2E; margin-bottom: 4px; }
.input { width: 100%; padding: 12px 14px; border: 1.5px solid #E5E7EB; border-radius: 10px; font-size: 16px; outline: none; transition: border-color 0.2s; }
.input:focus { border-color: #FF6B35; }
.row { display: flex; gap: 10px; }
.row > * { flex: 1; }
.swap-btn { width: 40px; height: 40px; border-radius: 20px; background: #FFE8DD; border: none; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; align-self: flex-end; margin-bottom: 2px; flex-shrink: 0; }
.btn { width: 100%; padding: 14px; border: none; border-radius: 12px; font-size: 16px; font-weight: 700; cursor: pointer; transition: all 0.2s; }
.btn-primary { background: #FF6B35; color: #fff; }
.btn-primary:active { background: #D4562A; transform: scale(0.98); }
.btn-primary:disabled { opacity: 0.5; }
.chips { display: flex; gap: 8px; overflow-x: auto; padding: 4px 0; -webkit-overflow-scrolling: touch; }
.chips::-webkit-scrollbar { display: none; }
.chip { padding: 6px 14px; border-radius: 20px; background: #F3F4F6; border: none; font-size: 13px; color: #6B7280; white-space: nowrap; cursor: pointer; }
.chip.active { background: #FF6B35; color: #fff; }
.sort-row { display: flex; gap: 8px; margin-bottom: 14px; }
.sort-btn { flex: 1; padding: 8px; border-radius: 8px; border: 1.5px solid #E5E7EB; background: none; font-size: 13px; cursor: pointer; }
.sort-btn.active { border-color: #FF6B35; background: #FFE8DD; color: #D4562A; font-weight: 600; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin: 16px 0 8px; }
.result-count { font-size: 16px; font-weight: 700; }
.direct-ref { font-size: 12px; color: #9CA3AF; }
.ticket-card { border: 1px solid #f0f0f0; border-radius: 14px; padding: 14px; margin-bottom: 12px; background: #fff; }
.ticket-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.outstation-badge { display: inline-flex; align-items: center; gap: 4px; background: #FFE8DD; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; color: #D4562A; }
.savings-badge { background: #10B981; color: #fff; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 700; }
.timeline { margin-bottom: 12px; }
.tl-section-label { font-size: 11px; font-weight: 700; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.5px; margin: 8px 0 4px; }
.tl-leg { display: flex; align-items: stretch; gap: 10px; padding: 2px 0; }
.tl-line { width: 20px; display: flex; flex-direction: column; align-items: center; }
.tl-dot { width: 10px; height: 10px; border-radius: 5px; flex-shrink: 0; z-index: 1; }
.tl-dot.out { background: #FF6B35; }
.tl-dot.main { background: #004E89; }
.tl-stem { width: 2px; flex: 1; background: #E5E7EB; }
.tl-body { flex: 1; padding-bottom: 6px; }
.tl-times { display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700; color: #1A1A2E; }
.tl-arrow { color: #9CA3AF; font-size: 12px; }
.tl-dur { font-size: 11px; font-weight: 500; color: #FF6B35; background: #FFE8DD; padding: 1px 6px; border-radius: 4px; }
.tl-next-day { font-size: 10px; font-weight: 700; color: #EF4444; background: #FEE2E2; padding: 1px 5px; border-radius: 4px; }
.tl-route { font-size: 13px; color: #6B7280; margin-top: 2px; }
.tl-meta { font-size: 11px; color: #9CA3AF; }
.tl-price { font-weight: 600; color: #1A1A2E; font-size: 13px; float: right; }
.tl-layover { display: flex; align-items: center; gap: 10px; padding: 0; }
.tl-layover-line { width: 20px; display: flex; flex-direction: column; align-items: center; }
.tl-layover-dash { width: 2px; height: 24px; background: repeating-linear-gradient(to bottom, #F59E0B 0px, #F59E0B 3px, transparent 3px, transparent 6px); }
.tl-layover-body { font-size: 12px; color: #F59E0B; font-weight: 600; padding: 4px 0; }
.tl-summary { display: flex; gap: 12px; margin-top: 6px; flex-wrap: wrap; }
.tl-summary-item { font-size: 11px; color: #6B7280; background: #F3F4F6; padding: 3px 8px; border-radius: 6px; }
.ticket-bottom { display: flex; justify-content: space-between; align-items: flex-end; border-top: 1px solid #f0f0f0; padding-top: 10px; }
.total-label { font-size: 11px; color: #9CA3AF; }
.total-price { font-size: 22px; font-weight: 700; color: #FF6B35; }
.compare { text-align: right; }
.direct-price { font-size: 13px; color: #9CA3AF; text-decoration: line-through; }
.save-amount { font-size: 13px; font-weight: 600; color: #10B981; }
.explain-banner { display: flex; align-items: center; gap: 8px; background: #E3F0FF; padding: 10px 14px; border-radius: 10px; margin-bottom: 14px; cursor: pointer; font-size: 13px; color: #004E89; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; align-items: flex-end; }
.modal { background: #fff; border-radius: 20px 20px 0 0; padding: 24px; max-height: 85vh; overflow-y: auto; width: 100%; max-width: 480px; margin: 0 auto; }
.modal h2 { font-size: 22px; font-weight: 700; margin-bottom: 12px; }
.modal p { font-size: 15px; color: #6B7280; line-height: 1.6; margin-bottom: 12px; }
.modal-route { background: #FFE8DD; padding: 14px; border-radius: 10px; margin-bottom: 16px; }
.modal-route p { color: #1A1A2E; margin-bottom: 6px; font-size: 15px; }
.history-item { display: flex; align-items: center; padding: 12px; border: 1px solid #f0f0f0; border-radius: 10px; margin-bottom: 8px; cursor: pointer; }
.history-item:active { background: #FFE8DD; }
.history-content { flex: 1; }
.history-route { font-size: 16px; font-weight: 700; }
.history-detail { font-size: 12px; color: #9CA3AF; margin-top: 2px; }
.history-price { font-size: 13px; color: #FF6B35; font-weight: 600; margin-top: 2px; }
.star-btn { width: 44px; height: 44px; border: none; background: none; font-size: 22px; cursor: pointer; }
.del-btn { width: 44px; height: 44px; border: none; background: none; font-size: 18px; cursor: pointer; color: #9CA3AF; }
.empty { text-align: center; padding: 60px 20px; color: #9CA3AF; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-text { font-size: 16px; font-weight: 600; margin-bottom: 8px; }
.empty-hint { font-size: 13px; }
.filter-row { display: flex; gap: 8px; margin-bottom: 12px; }
`

// ─── Mock data ──────────────────────────────────────
// (reuse from mock.ts)

const AIRPORTS = [
  { code: 'TPE', label: '台北桃園' },
  { code: 'NRT', label: '東京成田' },
  { code: 'KIX', label: '大阪關西' },
  { code: 'ICN', label: '首爾仁川' },
  { code: 'BKK', label: '曼谷' },
  { code: 'SIN', label: '新加坡' },
  { code: 'HKG', label: '香港' },
  { code: 'CDG', label: '巴黎' },
  { code: 'LAX', label: '洛杉磯' },
]

// ─── History ────────────────────────────────────────
interface HistoryItem {
  id: string; origin: string; destination: string;
  departure: string; return_: string; passengers: number;
  bestPrice: number | null; directPrice: number | null;
  count: number; saved: boolean; time: string;
}

function loadHistory(): HistoryItem[] {
  try { return JSON.parse(localStorage.getItem('search_history') || '[]') } catch { return [] }
}
function saveHistory(h: HistoryItem[]) { localStorage.setItem('search_history', JSON.stringify(h)) }

// ─── App ────────────────────────────────────────────
type Tab = 'search' | 'history'

export default function App() {
  const [tab, setTab] = useState<Tab>('search')
  const [origin, setOrigin] = useState('TPE')
  const [dest, setDest] = useState('')
  const [dep, setDep] = useState('')
  const [ret, setRet] = useState('')
  const [pax, setPax] = useState('1')
  const [sort, setSort] = useState<'price' | 'transit'>('price')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<OutstationTicket[]>([])
  const [directPrice, setDirectPrice] = useState<number | null>(null)
  const [showExplain, setShowExplain] = useState(false)
  const [history, setHistory] = useState<HistoryItem[]>(loadHistory)

  const swap = () => { setOrigin(dest); setDest(origin) }

  const search = async () => {
    if (!origin || !dest || !dep || !ret) { alert('請填寫完整資訊'); return }
    setLoading(true)
    // Try real API, fallback to mock
    let data: SearchResult
    try {
      const API = import.meta.env.VITE_API_URL
      if (!API) throw new Error('no api')
      const res = await fetch(`${API}/tickets/search`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ origin, destination: dest, departure_date: dep, return_date: ret, passengers: +pax, sort_by: sort === 'price' ? 'price' : 'transit_time' }),
      })
      if (!res.ok) throw new Error()
      data = await res.json()
    } catch {
      data = mockSearch(origin, dest, dep, ret, +pax || 1, sort)
    }
    setResults(data.results)
    setDirectPrice(data.direct_price)
    // Save to history
    const best = data.results.length > 0 ? Math.min(...data.results.map(r => r.total_price)) : null
    const item: HistoryItem = {
      id: Date.now().toString(), origin, destination: dest,
      departure: dep, return_: ret, passengers: +pax || 1,
      bestPrice: best, directPrice: data.direct_price,
      count: data.results.length, saved: false,
      time: new Date().toLocaleString('zh-TW'),
    }
    const updated = [item, ...history].slice(0, 50)
    setHistory(updated); saveHistory(updated)
    setLoading(false)
  }

  const toggleStar = (id: string) => {
    const updated = history.map(h => h.id === id ? { ...h, saved: !h.saved } : h)
    setHistory(updated); saveHistory(updated)
  }
  const deleteItem = (id: string) => {
    const updated = history.filter(h => h.id !== id)
    setHistory(updated); saveHistory(updated)
  }
  const reSearch = (h: HistoryItem) => {
    setOrigin(h.origin); setDest(h.destination); setDep(h.departure); setRet(h.return_); setPax(String(h.passengers))
    setTab('search')
  }

  return (
    <>
      <style>{CSS}</style>
      <div className="app">
        <div className="header">
          <h1>✈️ AirTicket 旅遊規劃</h1>
          <p>外站票（四段票）搜尋 — 找到最便宜的飛法</p>
        </div>

        <div className="tabs">
          <button className={`tab ${tab === 'search' ? 'active' : ''}`} onClick={() => setTab('search')}>🔍 搜機票</button>
          <button className={`tab ${tab === 'history' ? 'active' : ''}`} onClick={() => setTab('history')}>📋 搜尋紀錄 {history.length > 0 && `(${history.length})`}</button>
        </div>

        <div className="content">
          {tab === 'search' && (
            <>
              <div className="explain-banner" onClick={() => setShowExplain(true)}>
                ❓ 什麼是外站票（四段票）？為什麼比較便宜？ →
              </div>

              <div className="card">
                <div className="row" style={{ alignItems: 'flex-end' }}>
                  <div className="form-group">
                    <label>出發地</label>
                    <input className="input" value={origin} onChange={e => setOrigin(e.target.value.toUpperCase())} placeholder="TPE" />
                  </div>
                  <button className="swap-btn" onClick={swap}>⇄</button>
                  <div className="form-group">
                    <label>目的地</label>
                    <input className="input" value={dest} onChange={e => setDest(e.target.value.toUpperCase())} placeholder="NRT" />
                  </div>
                </div>

                <div className="chips">
                  {AIRPORTS.filter(a => a.code !== origin).map(a => (
                    <button key={a.code} className={`chip ${dest === a.code ? 'active' : ''}`} onClick={() => setDest(a.code)}>{a.label}</button>
                  ))}
                </div>

                <div className="row" style={{ marginTop: 14 }}>
                  <div className="form-group">
                    <label>去程日期</label>
                    <input className="input" type="date" value={dep} onChange={e => setDep(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label>回程日期</label>
                    <input className="input" type="date" value={ret} onChange={e => setRet(e.target.value)} />
                  </div>
                </div>

                <div className="row">
                  <div className="form-group">
                    <label>人數</label>
                    <input className="input" type="number" min="1" max="9" value={pax} onChange={e => setPax(e.target.value)} style={{ width: 80 }} />
                  </div>
                  <div className="form-group">
                    <label>排序</label>
                    <div className="sort-row">
                      <button className={`sort-btn ${sort === 'price' ? 'active' : ''}`} onClick={() => setSort('price')}>💰 價格</button>
                      <button className={`sort-btn ${sort === 'transit' ? 'active' : ''}`} onClick={() => setSort('transit')}>⏱️ 轉機</button>
                    </div>
                  </div>
                </div>

                <button className="btn btn-primary" onClick={search} disabled={loading}>
                  {loading ? '搜尋中...' : '🔍 搜尋外站票'}
                </button>
              </div>

              {results.length > 0 && (
                <>
                  <div className="result-header">
                    <span className="result-count">找到 {results.length} 個外站票組合</span>
                    {directPrice && <span className="direct-ref">直飛參考 ${directPrice.toLocaleString()}</span>}
                  </div>
                  {results.map((t, i) => (
                    <div className="ticket-card" key={i}>
                      <div className="ticket-top">
                        <span className="outstation-badge">✈️ 外站：{t.outstation_city_name} ({t.outstation_city})</span>
                        {t.savings_percent && t.savings_percent > 0 && <span className="savings-badge">省 {t.savings_percent}%</span>}
                      </div>

                      {/* Timeline */}
                      <div className="timeline">
                        <div className="tl-section-label">✈ 去程 — {t.outbound_hours}h</div>
                        {/* Leg 1 */}
                        <div className="tl-leg">
                          <div className="tl-line"><div className="tl-dot out" /><div className="tl-stem" /></div>
                          <div className="tl-body">
                            <div className="tl-times">
                              {t.legs[0].departure_time} <span className="tl-arrow">→</span> {t.legs[0].arrival_time}
                              <span className="tl-dur">{Math.floor(t.legs[0].flight_duration_minutes/60)}h {t.legs[0].flight_duration_minutes%60}m</span>
                              {t.legs[0].next_day && <span className="tl-next-day">+1天</span>}
                            </div>
                            <div className="tl-route">{t.legs[0].origin} → {t.legs[0].destination}</div>
                            <div className="tl-meta">{t.legs[0].airline} {t.legs[0].flight_number} <span className="tl-price">${t.legs[0].price.toLocaleString()}</span></div>
                          </div>
                        </div>
                        {/* Layover 1 */}
                        {t.layovers[0] && (
                          <div className="tl-layover">
                            <div className="tl-layover-line"><div className="tl-layover-dash" /></div>
                            <div className="tl-layover-body">⏳ 轉機等待 {t.layovers[0].duration_display}（{t.layovers[0].city}）</div>
                          </div>
                        )}
                        {/* Leg 2 */}
                        <div className="tl-leg">
                          <div className="tl-line"><div className="tl-dot main" /><div className="tl-stem" /></div>
                          <div className="tl-body">
                            <div className="tl-times">
                              {t.legs[1].departure_time} <span className="tl-arrow">→</span> {t.legs[1].arrival_time}
                              <span className="tl-dur">{Math.floor(t.legs[1].flight_duration_minutes/60)}h {t.legs[1].flight_duration_minutes%60}m</span>
                              {t.legs[1].next_day && <span className="tl-next-day">+1天</span>}
                            </div>
                            <div className="tl-route">{t.legs[1].origin} → {t.legs[1].destination}</div>
                            <div className="tl-meta">{t.legs[1].airline} {t.legs[1].flight_number} <span className="tl-price">${t.legs[1].price.toLocaleString()}</span></div>
                          </div>
                        </div>

                        <div className="tl-section-label" style={{marginTop:12}}>✈ 回程 — {t.return_hours}h</div>
                        {/* Leg 3 */}
                        <div className="tl-leg">
                          <div className="tl-line"><div className="tl-dot main" /><div className="tl-stem" /></div>
                          <div className="tl-body">
                            <div className="tl-times">
                              {t.legs[2].departure_time} <span className="tl-arrow">→</span> {t.legs[2].arrival_time}
                              <span className="tl-dur">{Math.floor(t.legs[2].flight_duration_minutes/60)}h {t.legs[2].flight_duration_minutes%60}m</span>
                              {t.legs[2].next_day && <span className="tl-next-day">+1天</span>}
                            </div>
                            <div className="tl-route">{t.legs[2].origin} → {t.legs[2].destination}</div>
                            <div className="tl-meta">{t.legs[2].airline} {t.legs[2].flight_number} <span className="tl-price">${t.legs[2].price.toLocaleString()}</span></div>
                          </div>
                        </div>
                        {/* Layover 2 */}
                        {t.layovers[1] && (
                          <div className="tl-layover">
                            <div className="tl-layover-line"><div className="tl-layover-dash" /></div>
                            <div className="tl-layover-body">⏳ 轉機等待 {t.layovers[1].duration_display}（{t.layovers[1].city}）</div>
                          </div>
                        )}
                        {/* Leg 4 */}
                        <div className="tl-leg">
                          <div className="tl-line"><div className="tl-dot out" /></div>
                          <div className="tl-body">
                            <div className="tl-times">
                              {t.legs[3].departure_time} <span className="tl-arrow">→</span> {t.legs[3].arrival_time}
                              <span className="tl-dur">{Math.floor(t.legs[3].flight_duration_minutes/60)}h {t.legs[3].flight_duration_minutes%60}m</span>
                              {t.legs[3].next_day && <span className="tl-next-day">+1天</span>}
                            </div>
                            <div className="tl-route">{t.legs[3].origin} → {t.legs[3].destination}</div>
                            <div className="tl-meta">{t.legs[3].airline} {t.legs[3].flight_number} <span className="tl-price">${t.legs[3].price.toLocaleString()}</span></div>
                          </div>
                        </div>

                        <div className="tl-summary">
                          <span className="tl-summary-item">🕐 總耗時 {t.total_journey_hours}h</span>
                          <span className="tl-summary-item">⏳ 轉機共 {Math.floor(t.total_transit_time_minutes/60)}h {t.total_transit_time_minutes%60}m</span>
                        </div>
                      </div>

                      <div className="ticket-bottom">
                        <div>
                          <div className="total-label">{+pax > 1 ? `${pax} 人總價` : '總價'}</div>
                          <div className="total-price">TWD {t.total_price.toLocaleString()}</div>
                        </div>
                        {t.savings && t.direct_price && (
                          <div className="compare">
                            <div className="direct-price">${t.direct_price.toLocaleString()}</div>
                            <div className="save-amount">省 ${t.savings.toLocaleString()}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </>
              )}
            </>
          )}

          {tab === 'history' && (
            <>
              {history.length === 0 ? (
                <div className="empty">
                  <div className="empty-icon">📋</div>
                  <div className="empty-text">還沒有搜尋紀錄</div>
                  <div className="empty-hint">搜尋外站票後，紀錄會自動保存在這裡</div>
                </div>
              ) : (
                history.map(h => (
                  <div className="history-item" key={h.id}>
                    <div className="history-content" onClick={() => reSearch(h)}>
                      <div className="history-route">{h.origin} → {h.destination}</div>
                      <div className="history-detail">{h.departure} ~ {h.return_} · {h.passengers}人 · {h.count}組合</div>
                      {h.bestPrice && <div className="history-price">最低 ${h.bestPrice.toLocaleString()}</div>}
                    </div>
                    <button className="star-btn" onClick={() => toggleStar(h.id)}>{h.saved ? '⭐' : '☆'}</button>
                    <button className="del-btn" onClick={() => deleteItem(h.id)}>✕</button>
                  </div>
                ))
              )}
            </>
          )}
        </div>

        {showExplain && (
          <div className="modal-overlay" onClick={() => setShowExplain(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>什麼是外站票（四段票）？</h2>
              <p>外站票是一種省錢的機票買法。不直接買「台北→東京」來回票，而是買「從另一個城市出發」的來回票，總共有四段航程：</p>
              <div className="modal-route">
                <p>1️⃣ 香港 → 台北（你先飛到出發地）</p>
                <p>2️⃣ 台北 → 東京（去程）</p>
                <p>3️⃣ 東京 → 台北（回程）</p>
                <p>4️⃣ 台北 → 香港（飛回外站城市）</p>
              </div>
              <p>💡 <strong>為什麼比較便宜？</strong><br/>航空公司在不同城市的定價不同，從某些城市出發的票價可能比台北出發便宜很多，即使加上往返外站城市的費用，總價還是更低！</p>
              <button className="btn btn-primary" onClick={() => setShowExplain(false)}>了解了！</button>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

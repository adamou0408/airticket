import { useState, useEffect, useRef, useCallback } from 'react'
import { mockSearch, type OutstationTicket, type SearchResult, type FlightLeg } from './mock'

const API = import.meta.env.VITE_API_URL || 'https://airticket-api.onrender.com/api'

type SearchMode = 'one_way' | 'round_trip' | 'outstation'

interface Airport { iata: string; name: string; city: string; country: string; city_zh: string; country_zh: string; popular: boolean }
interface FlightItem { airline: string; flight_number: string; origin: string; destination: string; departure_date: string; departure_time: string; arrival_date: string; arrival_time: string; duration_minutes: number; price: number; source: string; next_day: boolean }

// ─── Helpers ────────────────────────────────────────
const WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六']
function fmtDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T00:00:00')
  const m = d.getMonth() + 1
  const day = d.getDate()
  const w = WEEKDAYS[d.getDay()]
  return `${m}/${day}（${w}）`
}
function fmtDurMin(min: number): string {
  const h = Math.floor(min / 60)
  const m = min % 60
  return h && m ? `${h}h ${m}m` : h ? `${h}h` : `${m}m`
}

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
.tl-date { font-size: 12px; font-weight: 600; color: #004E89; margin-bottom: 2px; }
.tl-times { display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700; color: #1A1A2E; flex-wrap: wrap; }
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
.mode-tabs { display: flex; gap: 0; margin-bottom: 14px; border-radius: 10px; overflow: hidden; border: 1.5px solid #E5E7EB; }
.mode-tab { flex: 1; padding: 10px 8px; text-align: center; font-size: 13px; font-weight: 600; color: #6B7280; border: none; background: #F9FAFB; cursor: pointer; }
.mode-tab.active { background: #FF6B35; color: #fff; }
.airport-wrap { position: relative; }
.airport-dropdown { position: absolute; top: 100%; left: 0; right: 0; background: #fff; border: 1.5px solid #FF6B35; border-top: none; border-radius: 0 0 10px 10px; max-height: 200px; overflow-y: auto; z-index: 20; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.airport-item { padding: 10px 14px; cursor: pointer; font-size: 14px; border-bottom: 1px solid #f0f0f0; }
.airport-item:hover, .airport-item:active { background: #FFE8DD; }
.airport-code { font-weight: 700; color: #FF6B35; margin-right: 6px; }
.airport-city { color: #1A1A2E; }
.airport-country { color: #9CA3AF; font-size: 12px; margin-left: 4px; }
.flight-card { border: 1px solid #f0f0f0; border-radius: 12px; padding: 12px; margin-bottom: 10px; background: #fff; }
.flight-top { display: flex; justify-content: space-between; align-items: center; }
.flight-airline { font-weight: 700; font-size: 14px; }
.flight-price { font-size: 18px; font-weight: 700; color: #FF6B35; }
.flight-times { display: flex; align-items: center; gap: 8px; margin: 8px 0 4px; font-size: 15px; font-weight: 600; }
.flight-detail { font-size: 12px; color: #9CA3AF; }
.source-badge { font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
.source-real { background: #D1FAE5; color: #065F46; }
.source-sim { background: #FEF3C7; color: #92400E; }
.section-title { font-size: 14px; font-weight: 700; color: #004E89; margin: 16px 0 8px; }
`

// ─── Mock data ──────────────────────────────────────
// (reuse from mock.ts)

// Airport search hook
function useAirportSearch() {
  const [airports, setAirports] = useState<Airport[]>([])
  useEffect(() => {
    fetch(`${API}/airports/all`).then(r => r.json()).then(d => setAirports(d.airports || [])).catch(() => {})
  }, [])
  const search = useCallback((q: string): Airport[] => {
    if (!q) return airports.filter(a => a.popular).slice(0, 15)
    const ql = q.toLowerCase()
    return airports.filter(a =>
      a.iata.toLowerCase().startsWith(ql) ||
      a.city.toLowerCase().includes(ql) ||
      a.city_zh.includes(q) ||
      a.country_zh.includes(q) ||
      a.country.toLowerCase().includes(ql)
    ).slice(0, 15)
  }, [airports])
  return { search, loaded: airports.length > 0 }
}

// ─── History ────────────────────────────────────────
interface HistoryItem {
  id: string; origin: string; destination: string;
  departure: string; return_: string; passengers: number;
  bestPrice: number | null; directPrice: number | null;
  count: number; saved: boolean; time: string;
  mode?: SearchMode; // 'one_way' | 'round_trip' | 'outstation'
}

const MODE_LABELS: Record<SearchMode, string> = { one_way: '單程', round_trip: '來回', outstation: '外站票' }
const MODE_ICONS: Record<SearchMode, string> = { one_way: '→', round_trip: '⇄', outstation: '✈' }

function loadHistory(): HistoryItem[] {
  try { return JSON.parse(localStorage.getItem('search_history') || '[]') } catch { return [] }
}
function saveHistory(h: HistoryItem[]) { localStorage.setItem('search_history', JSON.stringify(h)) }

// ─── App ────────────────────────────────────────────
type Tab = 'search' | 'history' | 'tracking'

interface TrackingItem { id: number; origin: string; destination: string; enabled: boolean; last_crawled_at: string | null; last_result_count: number }

export default function App() {
  const [tab, setTab] = useState<Tab>('search')
  const [searchMode, setSearchMode] = useState<SearchMode>('round_trip')
  const [origin, setOrigin] = useState('TPE')
  const [originText, setOriginText] = useState('TPE')
  const [dest, setDest] = useState('')
  const [destText, setDestText] = useState('')
  const [showOriginDrop, setShowOriginDrop] = useState(false)
  const [showDestDrop, setShowDestDrop] = useState(false)
  const [dep, setDep] = useState('')
  const [ret, setRet] = useState('')
  const [pax, setPax] = useState('1')
  const [sort, setSort] = useState<'price' | 'transit'>('price')
  const [loading, setLoading] = useState(false)
  // Outstation results
  const [results, setResults] = useState<OutstationTicket[]>([])
  const [directPrice, setDirectPrice] = useState<number | null>(null)
  // Flight results (one-way / round-trip)
  const [flightResults, setFlightResults] = useState<FlightItem[]>([])
  const [returnFlights, setReturnFlights] = useState<FlightItem[]>([])
  const [showExplain, setShowExplain] = useState(false)
  const [history, setHistory] = useState<HistoryItem[]>(loadHistory)

  const { search: searchAirport, loaded: airportsLoaded } = useAirportSearch()

  const selectOrigin = (a: Airport) => { setOrigin(a.iata); setOriginText(`${a.iata} ${a.city_zh || a.city}`); setShowOriginDrop(false) }
  const selectDest = (a: Airport) => { setDest(a.iata); setDestText(`${a.iata} ${a.city_zh || a.city}`); setShowDestDrop(false) }

  // Auto-resolve typed text to IATA code when input loses focus
  const resolveOrigin = () => {
    setTimeout(() => {
      setShowOriginDrop(false)
      if (!originText) { setOrigin(''); return }
      // If already a valid IATA (3 uppercase letters), use it
      const upper = originText.trim().toUpperCase()
      if (/^[A-Z]{3}$/.test(upper)) { setOrigin(upper); return }
      // Try to find a match from the first search result
      const matches = searchAirport(originText)
      if (matches.length > 0) { selectOrigin(matches[0]) }
    }, 200)
  }
  const resolveDest = () => {
    setTimeout(() => {
      setShowDestDrop(false)
      if (!destText) { setDest(''); return }
      const upper = destText.trim().toUpperCase()
      if (/^[A-Z]{3}$/.test(upper)) { setDest(upper); return }
      const matches = searchAirport(destText)
      if (matches.length > 0) { selectDest(matches[0]) }
    }, 200)
  }

  const swap = () => {
    const tmpCode = origin; const tmpText = originText
    setOrigin(dest); setOriginText(destText)
    setDest(tmpCode); setDestText(tmpText)
  }

  const search = async () => {
    if (!origin || !dest || !dep) {
      const missing = []
      if (!origin) missing.push('出發地')
      if (!dest) missing.push('目的地')
      if (!dep) missing.push('日期')
      alert(`請填寫：${missing.join('、')}\n\n💡 提示：在機場欄位輸入城市名（如「東京」）或機場代碼（如「NRT」），然後從下拉選單選擇`)
      return
    }
    if (searchMode !== 'one_way' && !ret) { alert('請填寫回程日期'); return }

    setLoading(true)
    setResults([]); setFlightResults([]); setReturnFlights([]); setDirectPrice(null)

    try {
      if (searchMode === 'outstation') {
        // Outstation ticket search
        let data: SearchResult
        try {
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
        _saveHistory(data.results.length, data.results.length > 0 ? Math.min(...data.results.map(r => r.total_price)) : null, data.direct_price)
      } else {
        // One-way or round-trip flight search
        try {
          const res = await fetch(`${API}/flights/search`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ origin, destination: dest, departure_date: dep, return_date: searchMode === 'round_trip' ? ret : undefined, passengers: +pax, trip_type: searchMode, sort_by: sort === 'price' ? 'price' : 'departure' }),
          })
          if (!res.ok) throw new Error()
          const data = await res.json()
          setFlightResults(data.outbound_flights || [])
          setReturnFlights(data.return_flights || [])
          const total = (data.outbound_flights?.length || 0) + (data.return_flights?.length || 0)
          _saveHistory(total, data.cheapest_outbound, data.cheapest_roundtrip)
        } catch {
          // Fallback: generate mock flight data for one-way/round-trip
          const mockFlights = (orig: string, dst: string, d: string): FlightItem[] => {
            const airlines = [['長榮航空','BR'],['星宇航空','JX'],['華航','CI'],['國泰航空','CX']]
            return airlines.map(([name, code], i) => ({
              airline: name, flight_number: `${code}${100+i*50+Math.floor(Math.random()*50)}`,
              origin: orig, destination: dst,
              departure_date: d, departure_time: `${8+i*3}:${['00','15','30','45'][i%4]}`,
              arrival_date: d, arrival_time: `${11+i*3}:${['30','45','00','15'][i%4]}`,
              duration_minutes: 150+Math.floor(Math.random()*120),
              price: (3000+Math.floor(Math.random()*8000))*(+pax||1),
              source: 'simulated', next_day: false,
            }))
          }
          const outbound = mockFlights(origin, dest, dep).sort((a,b) => a.price - b.price)
          setFlightResults(outbound)
          if (searchMode === 'round_trip' && ret) {
            const retFlights = mockFlights(dest, origin, ret).sort((a,b) => a.price - b.price)
            setReturnFlights(retFlights)
          }
          const bestPrice = outbound.length > 0 ? outbound[0].price : null
          _saveHistory(outbound.length, bestPrice, null)
        }
      }
    } finally {
      setLoading(false)
    }
  }

  const _saveHistory = (count: number, bestPrice: number | null, directPrice: number | null) => {
    const item: HistoryItem = {
      id: Date.now().toString(), origin, destination: dest,
      departure: dep, return_: ret, passengers: +pax || 1,
      bestPrice, directPrice, count, saved: false,
      time: new Date().toLocaleString('zh-TW'),
      mode: searchMode,
    }
    const updated = [item, ...history].slice(0, 50)
    setHistory(updated); saveHistory(updated)
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

  // ─── Tracking (D.3) ───────────────
  const [trackingList, setTrackingList] = useState<TrackingItem[]>([])
  const [trackOrigin, setTrackOrigin] = useState('')
  const [trackDest, setTrackDest] = useState('')

  const loadTracking = async () => {
    try {
      // For demo: use localStorage since we might not have auth token
      const saved = localStorage.getItem('tracking_routes')
      if (saved) setTrackingList(JSON.parse(saved))
    } catch {}
  }
  useEffect(() => { loadTracking() }, [])

  const addTracking = () => {
    if (!trackOrigin || !trackDest) return
    const item: TrackingItem = {
      id: Date.now(), origin: trackOrigin.toUpperCase(), destination: trackDest.toUpperCase(),
      enabled: true, last_crawled_at: null, last_result_count: 0,
    }
    const updated = [item, ...trackingList.filter(t => !(t.origin === item.origin && t.destination === item.destination))]
    setTrackingList(updated)
    localStorage.setItem('tracking_routes', JSON.stringify(updated))
    setTrackOrigin(''); setTrackDest('')

    // Also try to save to backend
    fetch(`${API}/crawl-schedules`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ origin: item.origin, destination: item.destination }),
    }).catch(() => {})
  }

  const removeTracking = (id: number) => {
    const updated = trackingList.filter(t => t.id !== id)
    setTrackingList(updated)
    localStorage.setItem('tracking_routes', JSON.stringify(updated))
  }

  const addCurrentToTracking = () => {
    if (!origin || !dest) return
    setTrackOrigin(origin); setTrackDest(dest)
    const item: TrackingItem = {
      id: Date.now(), origin, destination: dest,
      enabled: true, last_crawled_at: null, last_result_count: 0,
    }
    const updated = [item, ...trackingList.filter(t => !(t.origin === item.origin && t.destination === item.destination))]
    setTrackingList(updated)
    localStorage.setItem('tracking_routes', JSON.stringify(updated))
    fetch(`${API}/crawl-schedules`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ origin, destination: dest }),
    }).catch(() => {})
  }

  // ─── Timeline rendering helpers ───────────────
  const renderLeg = (leg: FlightLeg, dotType: 'out' | 'main', hasStem: boolean) => (
    <div className="tl-leg">
      <div className="tl-line">
        <div className={`tl-dot ${dotType}`} />
        {hasStem && <div className="tl-stem" />}
      </div>
      <div className="tl-body">
        <div className="tl-date">{fmtDate(leg.departure_date)}</div>
        <div className="tl-times">
          {leg.departure_time} <span className="tl-arrow">→</span> {leg.arrival_time}
          {leg.next_day && <span className="tl-next-day">+1天 {fmtDate(leg.arrival_date)}</span>}
          <span className="tl-dur">{fmtDurMin(leg.flight_duration_minutes)}</span>
        </div>
        <div className="tl-route">{leg.origin} → {leg.destination}</div>
        <div className="tl-meta">{leg.airline} {leg.flight_number} <span className="tl-price">${leg.price.toLocaleString()}</span></div>
      </div>
    </div>
  )

  const renderLayover = (layover: { city: string; duration_display: string }) => (
    <div className="tl-layover">
      <div className="tl-layover-line"><div className="tl-layover-dash" /></div>
      <div className="tl-layover-body">⏳ 轉機等待 {layover.duration_display}（{layover.city}）</div>
    </div>
  )

  return (
    <>
      <style>{CSS}</style>
      <div className="app">
        <div className="header">
          <h1>✈️ AirTicket 旅遊規劃</h1>
          <p>機票搜尋 — 單程 · 來回 · 外站票{airportsLoaded ? ` · ${searchAirport('').length > 100 ? '6000+' : ''} 全球機場` : ''}</p>
        </div>

        <div className="tabs">
          <button className={`tab ${tab === 'search' ? 'active' : ''}`} onClick={() => setTab('search')}>🔍 搜機票</button>
          <button className={`tab ${tab === 'history' ? 'active' : ''}`} onClick={() => setTab('history')}>📋 紀錄 {history.length > 0 && `(${history.length})`}</button>
          <button className={`tab ${tab === 'tracking' ? 'active' : ''}`} onClick={() => setTab('tracking')}>📌 追蹤 {trackingList.length > 0 && `(${trackingList.length})`}</button>
        </div>

        <div className="content">
          {tab === 'search' && (
            <>
              <div className="explain-banner" onClick={() => setShowExplain(true)}>
                ❓ 什麼是外站票（四段票）？為什麼比較便宜？ →
              </div>

              <div className="card">
                {/* Search mode tabs */}
                <div className="mode-tabs">
                  <button className={`mode-tab ${searchMode === 'one_way' ? 'active' : ''}`} onClick={() => setSearchMode('one_way')}>單程</button>
                  <button className={`mode-tab ${searchMode === 'round_trip' ? 'active' : ''}`} onClick={() => setSearchMode('round_trip')}>來回</button>
                  <button className={`mode-tab ${searchMode === 'outstation' ? 'active' : ''}`} onClick={() => setSearchMode('outstation')}>外站票</button>
                </div>

                {/* Airport inputs with search */}
                <div className="row" style={{ alignItems: 'flex-end' }}>
                  <div className="form-group airport-wrap">
                    <label>出發地</label>
                    <input className="input" value={originText} placeholder="搜尋機場（輸入城市或代碼）"
                      onChange={e => { setOriginText(e.target.value); setOrigin(''); setShowOriginDrop(true) }}
                      onFocus={() => setShowOriginDrop(true)}
                      onBlur={resolveOrigin} />
                    {showOriginDrop && (
                      <div className="airport-dropdown">
                        {searchAirport(originText).map(a => (
                          <div key={a.iata} className="airport-item" onMouseDown={() => selectOrigin(a)}>
                            <span className="airport-code">{a.iata}</span>
                            <span className="airport-city">{a.city_zh || a.city}</span>
                            <span className="airport-country">{a.country_zh || a.country}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <button className="swap-btn" onClick={swap}>⇄</button>
                  <div className="form-group airport-wrap">
                    <label>目的地</label>
                    <input className="input" value={destText} placeholder="搜尋機場（輸入城市或代碼）"
                      onChange={e => { setDestText(e.target.value); setDest(''); setShowDestDrop(true) }}
                      onFocus={() => setShowDestDrop(true)}
                      onBlur={resolveDest} />
                    {showDestDrop && (
                      <div className="airport-dropdown">
                        {searchAirport(destText).map(a => (
                          <div key={a.iata} className="airport-item" onMouseDown={() => selectDest(a)}>
                            <span className="airport-code">{a.iata}</span>
                            <span className="airport-city">{a.city_zh || a.city}</span>
                            <span className="airport-country">{a.country_zh || a.country}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Dates */}
                <div className="row" style={{ marginTop: 14 }}>
                  <div className="form-group">
                    <label>去程日期</label>
                    <input className="input" type="date" value={dep} onChange={e => setDep(e.target.value)} />
                  </div>
                  {searchMode !== 'one_way' && (
                    <div className="form-group">
                      <label>回程日期</label>
                      <input className="input" type="date" value={ret} onChange={e => setRet(e.target.value)} />
                    </div>
                  )}
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
                      <button className={`sort-btn ${sort === 'transit' ? 'active' : ''}`} onClick={() => setSort('transit')}>⏱️ {searchMode === 'outstation' ? '轉機' : '時間'}</button>
                    </div>
                  </div>
                </div>

                <button className="btn btn-primary" onClick={search} disabled={loading}>
                  {loading ? '搜尋中...' : searchMode === 'outstation' ? '🔍 搜尋外站票' : searchMode === 'one_way' ? '🔍 搜尋單程機票' : '🔍 搜尋來回機票'}
                </button>
              </div>

              {/* Flight results (one-way / round-trip) */}
              {flightResults.length > 0 && (
                <>
                  <div className="section-title">✈ 去程航班 ({flightResults.length})</div>
                  {flightResults.map((f, i) => (
                    <div className="flight-card" key={`out-${i}`}>
                      <div className="flight-top">
                        <span className="flight-airline">{f.airline} <span style={{fontWeight:400, color:'#9CA3AF', fontSize:12}}>{f.flight_number}</span></span>
                        <span className="flight-price">TWD {f.price.toLocaleString()}</span>
                      </div>
                      <div className="flight-times">
                        <span>{fmtDate(f.departure_date)} {f.departure_time}</span>
                        <span style={{color:'#9CA3AF'}}>→</span>
                        <span>{f.arrival_time}{f.next_day ? ' (+1天)' : ''}</span>
                        <span className="tl-dur">{fmtDurMin(f.duration_minutes)}</span>
                      </div>
                      <div className="flight-detail">
                        {f.origin} → {f.destination}
                        <span className={`source-badge ${f.source === 'simulated' ? 'source-sim' : 'source-real'}`} style={{marginLeft:8}}>
                          {f.source === 'simulated' ? '⚠️ 模擬' : `✅ ${f.source}`}
                        </span>
                      </div>
                    </div>
                  ))}
                  {returnFlights.length > 0 && (
                    <>
                      <div className="section-title">✈ 回程航班 ({returnFlights.length})</div>
                      {returnFlights.map((f, i) => (
                        <div className="flight-card" key={`ret-${i}`}>
                          <div className="flight-top">
                            <span className="flight-airline">{f.airline} <span style={{fontWeight:400, color:'#9CA3AF', fontSize:12}}>{f.flight_number}</span></span>
                            <span className="flight-price">TWD {f.price.toLocaleString()}</span>
                          </div>
                          <div className="flight-times">
                            <span>{fmtDate(f.departure_date)} {f.departure_time}</span>
                            <span style={{color:'#9CA3AF'}}>→</span>
                            <span>{f.arrival_time}{f.next_day ? ' (+1天)' : ''}</span>
                            <span className="tl-dur">{fmtDurMin(f.duration_minutes)}</span>
                          </div>
                          <div className="flight-detail">
                            {f.origin} → {f.destination}
                            <span className={`source-badge ${f.source === 'simulated' ? 'source-sim' : 'source-real'}`} style={{marginLeft:8}}>
                              {f.source === 'simulated' ? '⚠️ 模擬' : `✅ ${f.source}`}
                            </span>
                          </div>
                        </div>
                      ))}
                    </>
                  )}
                </>
              )}

              {/* Outstation results */}
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
                        {/* Outbound */}
                        <div className="tl-section-label">✈ 去程 — 共 {t.outbound_hours}h</div>
                        {renderLeg(t.legs[0], 'out', true)}
                        {t.layovers[0] && renderLayover(t.layovers[0])}
                        {renderLeg(t.legs[1], 'main', true)}

                        {/* Return */}
                        <div className="tl-section-label" style={{marginTop:12}}>✈ 回程 — 共 {t.return_hours}h</div>
                        {renderLeg(t.legs[2], 'main', true)}
                        {t.layovers[1] && renderLayover(t.layovers[1])}
                        {renderLeg(t.legs[3], 'out', false)}

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

              {/* Add to tracking button — shows after any search with results */}
              {(results.length > 0 || flightResults.length > 0) && origin && dest && (
                <button className="btn btn-primary" style={{marginTop:12, background:'#004E89'}} onClick={addCurrentToTracking}>
                  📌 加入每日追蹤 {origin} → {dest}
                </button>
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
                    <div className="history-content" onClick={() => { if (h.mode) setSearchMode(h.mode); reSearch(h) }}>
                      <div className="history-route">
                        {h.mode && <span style={{fontSize:11, background: h.mode === 'outstation' ? '#FFE8DD' : h.mode === 'one_way' ? '#E3F0FF' : '#D1FAE5', color: h.mode === 'outstation' ? '#D4562A' : h.mode === 'one_way' ? '#004E89' : '#065F46', padding:'2px 6px', borderRadius:4, marginRight:6, fontWeight:600}}>{MODE_LABELS[h.mode]}</span>}
                        {h.origin} {MODE_ICONS[h.mode || 'round_trip']} {h.destination}
                      </div>
                      <div className="history-detail">{h.departure}{h.return_ ? ` ~ ${h.return_}` : ''} · {h.passengers}人 · {h.count}{h.mode === 'outstation' ? '組合' : '航班'}</div>
                      {h.bestPrice && <div className="history-price">最低 ${h.bestPrice.toLocaleString()}</div>}
                    </div>
                    <button className="star-btn" onClick={() => toggleStar(h.id)}>{h.saved ? '⭐' : '☆'}</button>
                    <button className="del-btn" onClick={() => deleteItem(h.id)}>✕</button>
                  </div>
                ))
              )}
            </>
          )}
          {tab === 'tracking' && (
            <>
              <div className="card">
                <div style={{fontSize:14, fontWeight:700, marginBottom:12}}>📌 我的追蹤航線</div>
                <p style={{fontSize:13, color:'#6B7280', marginBottom:14}}>
                  加入追蹤的航線，系統會每天自動爬取最新票價，讓你搜尋時直接看到真實資料。
                </p>

                {/* Add new tracking */}
                <div className="row" style={{marginBottom:12}}>
                  <input className="input" value={trackOrigin} onChange={e => setTrackOrigin(e.target.value.toUpperCase())} placeholder="出發地 TPE" />
                  <input className="input" value={trackDest} onChange={e => setTrackDest(e.target.value.toUpperCase())} placeholder="目的地 NRT" />
                  <button className="btn btn-primary" style={{width:'auto', padding:'10px 16px', flexShrink:0}} onClick={addTracking}>＋</button>
                </div>
              </div>

              {trackingList.length === 0 ? (
                <div className="empty">
                  <div className="empty-icon">📌</div>
                  <div className="empty-text">還沒有追蹤的航線</div>
                  <div className="empty-hint">搜尋機票後點「加入每日追蹤」，或在上方手動新增</div>
                </div>
              ) : (
                trackingList.map(t => (
                  <div className="history-item" key={t.id}>
                    <div className="history-content">
                      <div className="history-route">{t.origin} → {t.destination}</div>
                      <div className="history-detail">
                        {t.last_crawled_at
                          ? `上次爬取：${new Date(t.last_crawled_at).toLocaleString('zh-TW')} · ${t.last_result_count} 筆`
                          : '尚未爬取'}
                      </div>
                    </div>
                    <span style={{fontSize:12, color: t.enabled ? '#10B981' : '#9CA3AF', fontWeight:600, padding:'0 8px'}}>
                      {t.enabled ? '啟用' : '暫停'}
                    </span>
                    <button className="del-btn" onClick={() => removeTracking(t.id)}>✕</button>
                  </div>
                ))
              )}

              <div style={{marginTop:16, fontSize:12, color:'#9CA3AF'}}>
                💡 系統預設追蹤熱門航線（TPE↔NRT、TPE↔KIX 等），不需手動新增。
              </div>
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

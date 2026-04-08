/**
 * Trips Tab — trip planning frontend with real-time collaboration.
 *
 * Spec: .req/specs/travel-planner-app/spec.md — US-18, US-7
 * Task: .req/specs/travel-planner-app/tasks.md — Task 3.1 (WebSocket 即時同步)
 */
import { useState, useEffect, useRef } from 'react'

const API = import.meta.env.VITE_API_URL || 'https://airticket-api.onrender.com/api'
const WS_URL = API.replace(/^http/, 'ws')

interface Trip { id: number; name: string; destination: string; start_date: string; end_date: string; budget: number | null; currency: string; status: string; owner_id: number; member_count: number; share_token: string }
interface TripDetail extends Trip { members: { user_id: number; role: string; confirmed: boolean }[]; items: Item[] }
interface Item { id: number; day_number: number; order: number; type: string; name: string; time: string; location: string; note: string; estimated_cost: number; created_by: number }

const TYPE_ICONS: Record<string, string> = { attraction: '🏛️', restaurant: '🍽️', transport: '✈️', accommodation: '🏨', other: '📌' }

export default function TripsTab({ token }: { token: string | null }) {
  const [trips, setTrips] = useState<Trip[]>([])
  const [selectedTrip, setSelectedTrip] = useState<TripDetail | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [destination, setDestination] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [budget, setBudget] = useState('')
  const [newItemName, setNewItemName] = useState('')
  const [newItemDay, setNewItemDay] = useState('1')
  const [newItemType, setNewItemType] = useState('other')
  const [newItemCost, setNewItemCost] = useState('')
  const [copied, setCopied] = useState(false)
  const [peers, setPeers] = useState(0)
  const [liveActivity, setLiveActivity] = useState('')
  const wsRef = useRef<WebSocket | null>(null)

  const headers = token ? { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' }

  useEffect(() => { if (token) loadTrips() }, [token])

  // WebSocket connection for real-time collaboration (Task 3.1)
  useEffect(() => {
    if (!selectedTrip || !token) {
      wsRef.current?.close()
      wsRef.current = null
      setPeers(0)
      return
    }

    const ws = new WebSocket(`${WS_URL}/trips/${selectedTrip.id}/ws?token=${token}`)
    wsRef.current = ws

    ws.onopen = () => console.log(`[ws] connected to trip ${selectedTrip.id}`)
    ws.onerror = (e) => console.warn('[ws] error', e)
    ws.onclose = () => { wsRef.current = null; setPeers(0) }

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        switch (msg.type) {
          case 'connected':
            setPeers(msg.peers || 1)
            break
          case 'presence':
            setPeers(msg.count || 0)
            if (msg.action === 'join') setLiveActivity('👋 有人加入編輯')
            if (msg.action === 'leave') setLiveActivity('👋 有人離開')
            break
          case 'item_added':
            setLiveActivity(`➕ 新增：${msg.item?.name || '項目'}`)
            loadTrip(selectedTrip.id)
            break
          case 'item_updated':
            setLiveActivity(`✏️ 更新：${msg.item?.name || '項目'}`)
            loadTrip(selectedTrip.id)
            break
          case 'item_deleted':
            setLiveActivity(`🗑️ 刪除項目`)
            loadTrip(selectedTrip.id)
            break
          case 'comment_added':
            setLiveActivity(`💬 新留言`)
            break
          case 'trip_finalized':
            setLiveActivity(`📋 行程已定案`)
            loadTrip(selectedTrip.id)
            break
        }
        if (msg.type !== 'pong' && msg.type !== 'connected') {
          setTimeout(() => setLiveActivity(''), 3000)
        }
      } catch {}
    }

    // Ping every 30s to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'ping' }))
    }, 30000)

    return () => {
      clearInterval(pingInterval)
      ws.close()
    }
  }, [selectedTrip?.id, token])

  const loadTrips = async () => {
    try {
      const res = await fetch(`${API}/trips`, { headers })
      if (res.ok) setTrips(await res.json())
    } catch {}
  }

  const loadTrip = async (id: number) => {
    try {
      const res = await fetch(`${API}/trips/${id}`, { headers })
      if (res.ok) setSelectedTrip(await res.json())
    } catch {}
  }

  const createTrip = async () => {
    if (!name || !destination || !startDate || !endDate) return
    try {
      const res = await fetch(`${API}/trips`, {
        method: 'POST', headers,
        body: JSON.stringify({ name, destination, start_date: startDate, end_date: endDate, budget: budget ? +budget : null }),
      })
      if (res.ok) { setShowCreate(false); setName(''); setDestination(''); loadTrips() }
    } catch {}
  }

  const addItem = async () => {
    if (!selectedTrip || !newItemName) return
    try {
      await fetch(`${API}/trips/${selectedTrip.id}/items`, {
        method: 'POST', headers,
        body: JSON.stringify({ day_number: +newItemDay, type: newItemType, name: newItemName, estimated_cost: newItemCost ? +newItemCost : 0 }),
      })
      setNewItemName(''); setNewItemCost('')
      loadTrip(selectedTrip.id)
    } catch {}
  }

  const deleteItem = async (itemId: number) => {
    if (!selectedTrip) return
    await fetch(`${API}/trips/${selectedTrip.id}/items/${itemId}`, { method: 'DELETE', headers })
    loadTrip(selectedTrip.id)
  }

  const finalize = async () => {
    if (!selectedTrip) return
    await fetch(`${API}/trips/${selectedTrip.id}/finalize`, { method: 'POST', headers })
    loadTrip(selectedTrip.id)
  }

  const copyInvite = () => {
    if (!selectedTrip) return
    // Share the read-only URL (public view) instead of API endpoint
    const url = `${window.location.origin}${window.location.pathname}?share=${selectedTrip.share_token}`
    navigator.clipboard.writeText(url)
    setCopied(true); setTimeout(() => setCopied(false), 2000)
  }

  // Export trip as formatted text (for copy/share to LINE, etc.)
  const exportAsText = (trip: TripDetail): string => {
    const lines: string[] = []
    lines.push(`✈️ ${trip.name}`)
    lines.push(`📍 ${trip.destination}`)
    lines.push(`📅 ${trip.start_date} ~ ${trip.end_date}`)
    if (trip.budget) lines.push(`💰 預算 ${trip.currency} ${trip.budget.toLocaleString()}`)
    lines.push(`👥 ${trip.members.length} 人`)
    lines.push('')

    // Group items by day
    const days: Record<number, Item[]> = {}
    trip.items.forEach(i => { (days[i.day_number] ||= []).push(i) })

    Object.keys(days).sort((a, b) => +a - +b).forEach(day => {
      lines.push(`─── Day ${day} ───`)
      days[+day].sort((a, b) => a.order - b.order).forEach(item => {
        const icon = TYPE_ICONS[item.type] || '📌'
        const time = item.time ? `${item.time} ` : ''
        const cost = item.estimated_cost ? ` ($${item.estimated_cost.toLocaleString()})` : ''
        lines.push(`${icon} ${time}${item.name}${cost}`)
        if (item.location) lines.push(`   📍 ${item.location}`)
        if (item.note) lines.push(`   📝 ${item.note}`)
      })
      lines.push('')
    })

    lines.push(`── by AirTicket 旅遊規劃 ──`)
    return lines.join('\n')
  }

  const [shareMsg, setShareMsg] = useState('')

  const copyTripText = async () => {
    if (!selectedTrip) return
    const text = exportAsText(selectedTrip)
    await navigator.clipboard.writeText(text)
    setShareMsg('✅ 已複製行程到剪貼簿')
    setTimeout(() => setShareMsg(''), 2500)
  }

  // Use native Web Share API if available (mobile)
  const shareViaSystem = async () => {
    if (!selectedTrip) return
    const text = exportAsText(selectedTrip)
    const url = `${window.location.origin}${window.location.pathname}?share=${selectedTrip.share_token}`
    if (navigator.share) {
      try {
        await navigator.share({ title: selectedTrip.name, text, url })
      } catch (e) { /* user cancelled */ }
    } else {
      // Fallback: copy to clipboard
      await navigator.clipboard.writeText(`${text}\n\n🔗 查看完整行程：${url}`)
      setShareMsg('✅ 已複製（含連結）')
      setTimeout(() => setShareMsg(''), 2500)
    }
  }

  // Print to PDF using browser's built-in print dialog
  const printToPdf = () => { window.print() }

  if (!token) return (
    <div className="empty">
      <div className="empty-icon">🔒</div>
      <div className="empty-text">請先登入</div>
      <div className="empty-hint">到「我的」頁面用電話號碼登入</div>
    </div>
  )

  // Trip detail view
  if (selectedTrip) {
    const days: Record<number, Item[]> = {}
    selectedTrip.items.forEach(i => { (days[i.day_number] ||= []).push(i) })
    const totalCost = selectedTrip.items.reduce((s, i) => s + i.estimated_cost, 0)

    return (
      <>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12}}>
          <button style={{background:'none',border:'none',fontSize:14,color:'#FF6B35',fontWeight:600,cursor:'pointer'}} onClick={() => setSelectedTrip(null)}>← 返回列表</button>
          {peers > 0 && (
            <div style={{display:'flex',alignItems:'center',gap:6,fontSize:12,color:'#10B981',fontWeight:600}}>
              <span style={{width:8,height:8,borderRadius:4,background:'#10B981',display:'inline-block',boxShadow:'0 0 0 4px rgba(16,185,129,0.2)'}} />
              {peers} 人在線
            </div>
          )}
        </div>

        {/* Live activity banner */}
        {liveActivity && (
          <div style={{background:'#FEF3C7',color:'#92400E',padding:'8px 12px',borderRadius:8,marginBottom:8,fontSize:13,fontWeight:600,textAlign:'center'}}>
            {liveActivity}
          </div>
        )}

        <div className="card">
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
            <div>
              <div style={{fontSize:18,fontWeight:700}}>{selectedTrip.name}</div>
              <div style={{fontSize:13,color:'#6B7280'}}>📍 {selectedTrip.destination} · {selectedTrip.start_date} ~ {selectedTrip.end_date}</div>
            </div>
            <span style={{fontSize:11,padding:'4px 8px',borderRadius:8,background:selectedTrip.status==='finalized'?'#D1FAE5':'#FEF3C7',color:selectedTrip.status==='finalized'?'#065F46':'#92400E',fontWeight:600}}>{selectedTrip.status==='finalized'?'已定案':'規劃中'}</span>
          </div>
          {selectedTrip.budget && (
            <div style={{marginTop:8,fontSize:13,color:'#6B7280'}}>💰 預算 {selectedTrip.currency} {selectedTrip.budget.toLocaleString()} · 預估 {totalCost.toLocaleString()}</div>
          )}
        </div>

        {/* Members */}
        <div className="card">
          <div style={{fontSize:14,fontWeight:700,marginBottom:8}}>👥 成員 ({selectedTrip.members.length})</div>
          {selectedTrip.members.map((m, i) => (
            <div key={i} style={{fontSize:13,padding:'4px 0',display:'flex',justifyContent:'space-between'}}>
              <span>用戶 {m.user_id}</span>
              <span style={{color:'#9CA3AF'}}>{m.role} {m.confirmed ? '✅' : ''}</span>
            </div>
          ))}
          <button className="btn btn-primary" style={{marginTop:8,fontSize:13,padding:10}} onClick={copyInvite}>{copied ? '✅ 已複製！' : '🔗 複製邀請連結'}</button>
        </div>

        {/* Share & Export (Task 5.x) */}
        <div className="card no-print">
          <div style={{fontSize:14,fontWeight:700,marginBottom:8}}>📤 分享行程</div>
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:8}}>
            <button className="btn" style={{border:'1.5px solid #FF6B35',color:'#FF6B35',padding:10,fontSize:13}} onClick={copyTripText}>📋 複製文字</button>
            <button className="btn" style={{border:'1.5px solid #004E89',color:'#004E89',padding:10,fontSize:13}} onClick={shareViaSystem}>📱 分享到 App</button>
            <button className="btn" style={{border:'1.5px solid #10B981',color:'#10B981',padding:10,fontSize:13}} onClick={printToPdf}>🖨️ 列印/存 PDF</button>
            <button className="btn" style={{border:'1.5px solid #9CA3AF',color:'#6B7280',padding:10,fontSize:13}} onClick={copyInvite}>🔗 唯讀連結</button>
          </div>
          {shareMsg && <div style={{marginTop:8,fontSize:13,color:'#10B981',fontWeight:600,textAlign:'center'}}>{shareMsg}</div>}
        </div>

        {/* Itinerary */}
        {Object.keys(days).sort((a,b) => +a - +b).map(day => (
          <div key={day}>
            <div className="section-title">Day {day}</div>
            {days[+day].sort((a,b) => a.order - b.order).map(item => (
              <div className="flight-card" key={item.id} style={{display:'flex',alignItems:'center',gap:10}}>
                <span style={{fontSize:20}}>{TYPE_ICONS[item.type] || '📌'}</span>
                <div style={{flex:1}}>
                  <div style={{fontWeight:600}}>{item.name}</div>
                  <div style={{fontSize:12,color:'#9CA3AF'}}>{item.time && `${item.time} · `}{item.location}</div>
                </div>
                {item.estimated_cost > 0 && <span style={{fontWeight:600,color:'#FF6B35'}}>$ {item.estimated_cost.toLocaleString()}</span>}
                <button className="del-btn" onClick={() => deleteItem(item.id)}>✕</button>
              </div>
            ))}
          </div>
        ))}

        {/* Add item */}
        {selectedTrip.status !== 'finalized' && (
          <div className="card">
            <div style={{fontSize:14,fontWeight:700,marginBottom:8}}>＋ 新增行程項目</div>
            <div className="row" style={{marginBottom:8}}>
              <select className="input" value={newItemDay} onChange={e => setNewItemDay(e.target.value)} style={{width:70,flex:'none'}}>
                {Array.from({length:30}, (_, i) => <option key={i+1} value={i+1}>Day {i+1}</option>)}
              </select>
              <select className="input" value={newItemType} onChange={e => setNewItemType(e.target.value)} style={{width:80,flex:'none'}}>
                <option value="attraction">🏛️ 景點</option>
                <option value="restaurant">🍽️ 餐廳</option>
                <option value="transport">✈️ 交通</option>
                <option value="accommodation">🏨 住宿</option>
                <option value="other">📌 其他</option>
              </select>
            </div>
            <div className="row" style={{marginBottom:8}}>
              <input className="input" value={newItemName} onChange={e => setNewItemName(e.target.value)} placeholder="名稱（如：淺草寺）" />
              <input className="input" value={newItemCost} onChange={e => setNewItemCost(e.target.value)} placeholder="預估 $" type="number" style={{width:90,flex:'none'}} />
            </div>
            <button className="btn btn-primary" onClick={addItem} style={{fontSize:14,padding:10}}>＋ 新增</button>
          </div>
        )}

        {/* Finalize */}
        {selectedTrip.status === 'planning' && (
          <button className="btn btn-primary" style={{background:'#004E89',marginTop:8}} onClick={finalize}>📋 發起定案</button>
        )}
      </>
    )
  }

  // Trip list view
  return (
    <>
      {showCreate ? (
        <div className="card">
          <div style={{fontSize:16,fontWeight:700,marginBottom:12}}>✈️ 建立新旅程</div>
          <div className="form-group"><label>旅程名稱</label><input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="例：日本東京行" /></div>
          <div className="form-group"><label>目的地</label><input className="input" value={destination} onChange={e => setDestination(e.target.value)} placeholder="例：東京" /></div>
          <div className="row">
            <div className="form-group"><label>出發日期</label><input className="input" type="date" value={startDate} onChange={e => setStartDate(e.target.value)} /></div>
            <div className="form-group"><label>回程日期</label><input className="input" type="date" value={endDate} onChange={e => setEndDate(e.target.value)} /></div>
          </div>
          <div className="form-group"><label>預算（選填）</label><input className="input" type="number" value={budget} onChange={e => setBudget(e.target.value)} placeholder="50000" /></div>
          <div className="row">
            <button className="btn" style={{border:'1.5px solid #E5E7EB',color:'#6B7280'}} onClick={() => setShowCreate(false)}>取消</button>
            <button className="btn btn-primary" onClick={createTrip}>建立</button>
          </div>
        </div>
      ) : (
        <button className="btn btn-primary" onClick={() => setShowCreate(true)} style={{marginBottom:12}}>＋ 建立新旅程</button>
      )}

      {trips.length === 0 && !showCreate ? (
        <div className="empty">
          <div className="empty-icon">🗺️</div>
          <div className="empty-text">還沒有旅程</div>
          <div className="empty-hint">建立第一個旅遊計畫，開始規劃行程！</div>
        </div>
      ) : trips.map(t => (
        <div className="flight-card" key={t.id} onClick={() => loadTrip(t.id)} style={{cursor:'pointer'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
            <div style={{fontWeight:700,fontSize:16}}>{t.name}</div>
            <span style={{fontSize:11,padding:'3px 8px',borderRadius:8,background:t.status==='finalized'?'#D1FAE5':'#FEF3C7',fontWeight:600}}>{t.status==='finalized'?'已定案':'規劃中'}</span>
          </div>
          <div style={{fontSize:13,color:'#6B7280',marginTop:4}}>📍 {t.destination} · {t.start_date} ~ {t.end_date}</div>
          <div style={{fontSize:12,color:'#9CA3AF',marginTop:4}}>👥 {t.member_count} 人</div>
        </div>
      ))}
    </>
  )
}

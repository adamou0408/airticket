/**
 * Expenses Tab — expense tracking + settlement frontend.
 * Spec: US-19 — 記帳拆帳前端頁面
 */
import { useState, useEffect } from 'react'

const API = import.meta.env.VITE_API_URL || 'https://airticket-api.onrender.com/api'

interface Expense { id: number; amount: number; currency: string; category: string; payer_id: number; note: string; created_at: string }
interface BudgetSummary { estimated_total: number; budget: number | null; actual_total: number; over_budget: boolean; by_category: Record<string, number>; currency: string }
interface SettlementEntry { from_user: number; to_user: number; amount: number; currency: string; settled: boolean }
interface Trip { id: number; name: string }

const CAT_ICONS: Record<string, string> = { transport: '🚗', accommodation: '🏨', food: '🍽️', ticket: '🎫', shopping: '🛍️', other: '📌' }
const CAT_COLORS: Record<string, string> = { transport: '#3B82F6', accommodation: '#8B5CF6', food: '#F59E0B', ticket: '#10B981', shopping: '#EC4899', other: '#6B7280' }

export default function ExpensesTab({ token, tripId }: { token: string | null; tripId: number | null }) {
  const [trips, setTrips] = useState<Trip[]>([])
  const [selectedTripId, setSelectedTripId] = useState<number | null>(tripId)
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [budget, setBudget] = useState<BudgetSummary | null>(null)
  const [settlement, setSettlement] = useState<SettlementEntry[]>([])
  const [view, setView] = useState<'expenses' | 'settlement'>('expenses')
  // Quick add
  const [amount, setAmount] = useState('')
  const [category, setCategory] = useState('food')
  const [note, setNote] = useState('')

  const headers = token ? { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' }

  useEffect(() => { if (token) loadTrips() }, [token])
  useEffect(() => { if (selectedTripId && token) { loadExpenses(); loadBudget(); loadSettlement() } }, [selectedTripId, token])

  const loadTrips = async () => { try { const r = await fetch(`${API}/trips`, { headers }); if (r.ok) { const data = await r.json(); setTrips(data); if (data.length > 0 && !selectedTripId) setSelectedTripId(data[0].id) } } catch {} }
  const loadExpenses = async () => { try { const r = await fetch(`${API}/trips/${selectedTripId}/expenses`, { headers }); if (r.ok) setExpenses(await r.json()) } catch {} }
  const loadBudget = async () => { try { const r = await fetch(`${API}/trips/${selectedTripId}/expenses/budget`, { headers }); if (r.ok) setBudget(await r.json()) } catch {} }
  const loadSettlement = async () => { try { const r = await fetch(`${API}/trips/${selectedTripId}/expenses/settlement`, { headers }); if (r.ok) { const d = await r.json(); setSettlement(d.entries || []) } } catch {} }

  const addExpense = async () => {
    if (!amount || !selectedTripId) return
    // Get current user ID (simplified: use payer_id = 0, backend will handle)
    try {
      const me = await fetch(`${API}/auth/me`, { headers }); const user = await me.json()
      await fetch(`${API}/trips/${selectedTripId}/expenses`, {
        method: 'POST', headers,
        body: JSON.stringify({ amount: +amount, payer_id: user.id, category, note }),
      })
      setAmount(''); setNote('')
      loadExpenses(); loadBudget(); loadSettlement()
    } catch {}
  }

  const markSettled = async (from: number, to: number) => {
    await fetch(`${API}/trips/${selectedTripId}/expenses/settlement/settle?from_user=${from}&to_user=${to}`, { method: 'PUT', headers })
    loadSettlement()
  }

  const copySettlement = () => {
    const text = settlement.map(e =>
      `${e.settled ? '✅' : '⏳'} 用戶${e.from_user} → 用戶${e.to_user}：${budget?.currency || 'TWD'} ${e.amount.toLocaleString()}`
    ).join('\n')
    navigator.clipboard.writeText(`💰 拆帳結算\n${text}`)
  }

  if (!token) return (
    <div className="empty">
      <div className="empty-icon">🔒</div>
      <div className="empty-text">請先登入</div>
    </div>
  )

  return (
    <>
      {/* Trip selector */}
      {trips.length > 0 && (
        <select className="input" value={selectedTripId || ''} onChange={e => setSelectedTripId(+e.target.value)} style={{marginBottom:12}}>
          <option value="">選擇旅程</option>
          {trips.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
      )}

      {!selectedTripId && (
        <div className="empty">
          <div className="empty-icon">💰</div>
          <div className="empty-text">選擇一個旅程來記帳</div>
        </div>
      )}

      {selectedTripId && (
        <>
          {/* Budget progress bar */}
          {budget && (
            <div className="card">
              <div style={{fontSize:14,fontWeight:700,marginBottom:8}}>💰 預算狀況</div>
              <div style={{display:'flex',justifyContent:'space-between',fontSize:13,marginBottom:4}}>
                <span>已花 {budget.currency} {budget.actual_total.toLocaleString()}</span>
                <span>{budget.budget ? `預算 ${budget.budget.toLocaleString()}` : '未設預算'}</span>
              </div>
              {budget.budget && (
                <div style={{background:'#F3F4F6',borderRadius:8,height:12,overflow:'hidden'}}>
                  <div style={{
                    width:`${Math.min((budget.actual_total / budget.budget) * 100, 100)}%`,
                    height:'100%', borderRadius:8,
                    background: budget.over_budget ? '#EF4444' : '#10B981',
                    transition:'width 0.3s',
                  }} />
                </div>
              )}
              {/* Category breakdown */}
              {Object.entries(budget.by_category).length > 0 && (
                <div style={{marginTop:10}}>
                  {Object.entries(budget.by_category).map(([cat, amt]) => (
                    <div key={cat} style={{display:'flex',alignItems:'center',gap:8,marginBottom:4}}>
                      <span style={{fontSize:14}}>{CAT_ICONS[cat] || '📌'}</span>
                      <div style={{flex:1,background:'#F3F4F6',borderRadius:4,height:8}}>
                        <div style={{width:`${budget.actual_total > 0 ? (amt / budget.actual_total) * 100 : 0}%`,height:'100%',borderRadius:4,background:CAT_COLORS[cat] || '#6B7280'}} />
                      </div>
                      <span style={{fontSize:12,color:'#6B7280',minWidth:60,textAlign:'right'}}>{amt.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* View toggle */}
          <div className="mode-tabs" style={{marginBottom:12}}>
            <button className={`mode-tab ${view === 'expenses' ? 'active' : ''}`} onClick={() => setView('expenses')}>📝 記帳</button>
            <button className={`mode-tab ${view === 'settlement' ? 'active' : ''}`} onClick={() => setView('settlement')}>🧮 拆帳</button>
          </div>

          {view === 'expenses' && (
            <>
              {/* Quick add */}
              <div className="card">
                <div style={{fontSize:14,fontWeight:700,marginBottom:8}}>⚡ 快速記帳</div>
                <input className="input" type="number" value={amount} onChange={e => setAmount(e.target.value)} placeholder="金額" style={{fontSize:28,fontWeight:700,textAlign:'center',marginBottom:8}} />
                <div className="chips" style={{marginBottom:8}}>
                  {Object.entries(CAT_ICONS).map(([cat, icon]) => (
                    <button key={cat} className={`chip ${category === cat ? 'active' : ''}`} onClick={() => setCategory(cat)}>{icon}</button>
                  ))}
                </div>
                <input className="input" value={note} onChange={e => setNote(e.target.value)} placeholder="備註（選填）" style={{marginBottom:8}} />
                <button className="btn btn-primary" onClick={addExpense}>💰 記帳</button>
              </div>

              {/* Expense list */}
              {expenses.map(e => (
                <div className="flight-card" key={e.id} style={{display:'flex',alignItems:'center',gap:10}}>
                  <span style={{fontSize:20}}>{CAT_ICONS[e.category] || '📌'}</span>
                  <div style={{flex:1}}>
                    <div style={{fontWeight:600}}>{e.currency} {e.amount.toLocaleString()}</div>
                    <div style={{fontSize:12,color:'#9CA3AF'}}>{e.note || e.category} · 用戶{e.payer_id}</div>
                  </div>
                  <span style={{fontSize:11,color:'#9CA3AF'}}>{new Date(e.created_at).toLocaleDateString('zh-TW')}</span>
                </div>
              ))}
            </>
          )}

          {view === 'settlement' && (
            <>
              <div className="card">
                <div style={{fontSize:14,fontWeight:700,marginBottom:8}}>🧮 拆帳結算</div>
                {settlement.length === 0 ? (
                  <div style={{textAlign:'center',color:'#9CA3AF',padding:20}}>✅ 大家都結清了！</div>
                ) : (
                  settlement.map((e, i) => (
                    <div key={i} style={{display:'flex',alignItems:'center',padding:'10px 0',borderBottom:'1px solid #f0f0f0',gap:8}}>
                      <div style={{flex:1}}>
                        <div style={{fontWeight:600}}>用戶{e.from_user} → 用戶{e.to_user}</div>
                        <div style={{fontSize:18,fontWeight:700,color:'#FF6B35'}}>{e.currency} {e.amount.toLocaleString()}</div>
                      </div>
                      <button
                        onClick={() => !e.settled && markSettled(e.from_user, e.to_user)}
                        style={{padding:'6px 12px',borderRadius:8,border:'none',fontSize:13,fontWeight:600,cursor:'pointer',
                          background: e.settled ? '#D1FAE5' : '#FEF3C7', color: e.settled ? '#065F46' : '#92400E'}}
                      >{e.settled ? '✅ 已結清' : '💸 標記結清'}</button>
                    </div>
                  ))
                )}
              </div>
              {settlement.length > 0 && (
                <button className="btn" style={{border:'1.5px solid #FF6B35',color:'#FF6B35',marginTop:8}} onClick={copySettlement}>📋 複製結算結果</button>
              )}
            </>
          )}
        </>
      )}
    </>
  )
}

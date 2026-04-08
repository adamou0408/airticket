/**
 * Read-only shared trip view.
 * Accessed via ?share={share_token} — no authentication required.
 *
 * Spec: .req/specs/travel-planner-app/spec.md — US-8
 * Task: .req/specs/travel-planner-app/tasks.md — Task 5.2 (read-only share link)
 */
import { useState, useEffect } from 'react'

const API = import.meta.env.VITE_API_URL || 'https://airticket-api.onrender.com/api'

const TYPE_ICONS: Record<string, string> = { attraction: '🏛️', restaurant: '🍽️', transport: '✈️', accommodation: '🏨', other: '📌' }

interface Item { id: number; day_number: number; order: number; type: string; name: string; time: string; location: string; note: string; estimated_cost: number }
interface SharedTrip { id: number; name: string; destination: string; start_date: string; end_date: string; budget: number | null; currency: string; status: string; members: { user_id: number; role: string }[]; items: Item[] }

export default function SharedTripView({ token }: { token: string }) {
  const [trip, setTrip] = useState<SharedTrip | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/share/${token}`)
      .then(async r => {
        if (!r.ok) throw new Error('分享連結無效或已過期')
        return r.json()
      })
      .then(data => { setTrip(data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [token])

  if (loading) return (
    <div className="empty" style={{padding:'80px 20px'}}>
      <div className="empty-icon">⏳</div>
      <div className="empty-text">載入中...</div>
    </div>
  )

  if (error || !trip) return (
    <div className="empty" style={{padding:'80px 20px'}}>
      <div className="empty-icon">🔒</div>
      <div className="empty-text">{error || '無法載入'}</div>
      <div className="empty-hint">此分享連結可能已過期或無效</div>
      <a href={window.location.pathname} style={{marginTop:16,color:'#FF6B35',fontWeight:600}}>← 返回首頁</a>
    </div>
  )

  // Group items by day
  const days: Record<number, Item[]> = {}
  trip.items.forEach(i => { (days[i.day_number] ||= []).push(i) })
  const totalCost = trip.items.reduce((s, i) => s + i.estimated_cost, 0)

  return (
    <div style={{padding:'16px'}}>
      {/* Banner: read-only indicator */}
      <div style={{background:'#E3F0FF',color:'#004E89',padding:'10px 14px',borderRadius:10,marginBottom:12,fontSize:13,textAlign:'center',fontWeight:600}}>
        👀 唯讀分享 · 你正在查看 {trip.name}
      </div>

      {/* Trip header */}
      <div className="card">
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start'}}>
          <div>
            <div style={{fontSize:22,fontWeight:700,marginBottom:4}}>{trip.name}</div>
            <div style={{fontSize:14,color:'#6B7280'}}>📍 {trip.destination}</div>
            <div style={{fontSize:14,color:'#6B7280'}}>📅 {trip.start_date} ~ {trip.end_date}</div>
            <div style={{fontSize:13,color:'#9CA3AF',marginTop:4}}>👥 {trip.members.length} 人</div>
          </div>
          <span style={{fontSize:11,padding:'4px 8px',borderRadius:8,background:trip.status==='finalized'?'#D1FAE5':'#FEF3C7',color:trip.status==='finalized'?'#065F46':'#92400E',fontWeight:600}}>{trip.status==='finalized'?'已定案':'規劃中'}</span>
        </div>
        {trip.budget && (
          <div style={{marginTop:8,fontSize:13,color:'#6B7280',borderTop:'1px solid #f0f0f0',paddingTop:8}}>
            💰 預算 {trip.currency} {trip.budget.toLocaleString()} · 預估 {totalCost.toLocaleString()}
          </div>
        )}
      </div>

      {/* Itinerary */}
      {Object.keys(days).length === 0 ? (
        <div className="empty">
          <div className="empty-icon">📝</div>
          <div className="empty-text">還沒有行程項目</div>
        </div>
      ) : Object.keys(days).sort((a, b) => +a - +b).map(day => (
        <div key={day}>
          <div className="section-title">Day {day}</div>
          {days[+day].sort((a, b) => a.order - b.order).map(item => (
            <div className="flight-card" key={item.id}>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <span style={{fontSize:22}}>{TYPE_ICONS[item.type] || '📌'}</span>
                <div style={{flex:1}}>
                  <div style={{fontWeight:700,fontSize:15}}>{item.name}</div>
                  {(item.time || item.location) && (
                    <div style={{fontSize:12,color:'#9CA3AF',marginTop:2}}>
                      {item.time && <span>🕐 {item.time}</span>}
                      {item.time && item.location && <span> · </span>}
                      {item.location && <span>📍 {item.location}</span>}
                    </div>
                  )}
                  {item.note && <div style={{fontSize:12,color:'#6B7280',marginTop:4,background:'#FEF3C7',padding:'4px 8px',borderRadius:4}}>📝 {item.note}</div>}
                </div>
                {item.estimated_cost > 0 && (
                  <div style={{fontWeight:700,color:'#FF6B35',fontSize:14}}>${item.estimated_cost.toLocaleString()}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      ))}

      {/* Footer */}
      <div className="no-print" style={{textAlign:'center',padding:'24px 0',color:'#9CA3AF',fontSize:12}}>
        <div>— AirTicket 旅遊規劃 —</div>
        <a href={window.location.pathname} style={{color:'#FF6B35',fontWeight:600,marginTop:8,display:'inline-block'}}>✈️ 搜尋便宜機票</a>
      </div>
    </div>
  )
}

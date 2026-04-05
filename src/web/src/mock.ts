export interface FlightLeg {
  origin: string; destination: string; airline: string;
  flight_number: string; departure_time: string; arrival_time: string;
  departure_date: string; arrival_date: string;
  flight_duration_minutes: number; price: number; next_day: boolean;
}

export interface LayoverInfo {
  city: string; duration_minutes: number; duration_display: string;
}

export interface OutstationTicket {
  outstation_city: string; outstation_city_name: string;
  legs: FlightLeg[]; layovers: LayoverInfo[];
  total_price: number; direct_price: number | null;
  savings: number | null; savings_percent: number | null;
  total_transit_time_minutes: number;
  total_journey_hours: number; outbound_hours: number; return_hours: number;
  currency: string;
}

export interface SearchResult {
  origin: string; destination: string; results: OutstationTicket[];
  direct_price: number | null; result_count: number;
}

function randInt(min: number, max: number) { return Math.floor(Math.random() * (max - min + 1)) + min }
function pad(n: number) { return n.toString().padStart(2, '0') }
function fmtDur(m: number) { const h = Math.floor(m / 60); const mm = m % 60; return h && mm ? `${h}h ${mm}m` : h ? `${h}h` : `${mm}m` }

function makeLeg(
  origin: string, dest: string, airline: string, code: string,
  depDate: string, depHour: number, durationMin: number, price: number,
): FlightLeg {
  const depMin = randInt(0, 3) * 15
  const arrTotal = depHour * 60 + depMin + durationMin
  const arrH = Math.floor(arrTotal / 60) % 24
  const arrM = arrTotal % 60
  const nextDay = arrTotal >= 24 * 60
  const arrDate = nextDay
    ? (() => { const d = new Date(depDate); d.setDate(d.getDate() + 1); return d.toISOString().slice(0, 10) })()
    : depDate
  return {
    origin, destination: dest, airline, flight_number: `${code}${randInt(100, 999)}`,
    departure_time: `${pad(depHour)}:${pad(depMin)}`,
    arrival_time: `${pad(arrH)}:${pad(arrM)}`,
    departure_date: depDate, arrival_date: arrDate,
    flight_duration_minutes: durationMin, price, next_day: nextDay,
  }
}

const OUTSTATIONS = [
  { code: 'MFM', name: '澳門', base: 2200, airline: '虎航 IT', alCode: 'IT', dur: 110 },
  { code: 'HKG', name: '香港', base: 2800, airline: '國泰 CX', alCode: 'CX', dur: 100 },
  { code: 'ICN', name: '首爾仁川', base: 3200, airline: '大韓 KE', alCode: 'KE', dur: 150 },
  { code: 'BKK', name: '曼谷', base: 3500, airline: '華航 CI', alCode: 'CI', dur: 225 },
  { code: 'SIN', name: '新加坡', base: 4000, airline: '星宇 JX', alCode: 'JX', dur: 270 },
  { code: 'KUL', name: '吉隆坡', base: 3300, airline: '亞航 AK', alCode: 'AK', dur: 255 },
]

export function mockSearch(
  origin: string, dest: string, dep: string, ret: string, pax: number, sort: string,
): SearchResult {
  const directPrice = 11000 * pax
  const mainDur = 150 + randInt(0, 120) // origin→dest flight duration

  const results: OutstationTicket[] = OUTSTATIONS
    .filter(o => o.code !== origin && o.code !== dest)
    .map(o => {
      const outPrice1 = o.base + randInt(0, 800)
      const mainPrice1 = 3500 + randInt(0, 2500)
      const mainPrice2 = mainPrice1 + randInt(-500, 500)
      const outPrice2 = o.base + randInt(-300, 500)

      // Outbound: leg1 departs early, leg2 departs after layover
      const leg1DepH = randInt(6, 10)
      const leg1 = makeLeg(o.code, origin, o.airline, o.alCode, dep, leg1DepH, o.dur, outPrice1)
      const leg1ArrMin = leg1DepH * 60 + o.dur
      const layover1Min = randInt(90, 240) // 1.5h-4h layover
      const leg2DepH = Math.floor((leg1ArrMin + layover1Min) / 60) % 24
      const leg2 = makeLeg(origin, dest, o.airline, o.alCode, dep, leg2DepH, mainDur, mainPrice1)

      // Return: leg3 departs afternoon, leg4 after layover
      const leg3DepH = randInt(14, 19)
      const leg3 = makeLeg(dest, origin, o.airline, o.alCode, ret, leg3DepH, mainDur, mainPrice2)
      const leg3ArrMin = leg3DepH * 60 + mainDur
      const layover2Min = randInt(90, 210)
      const leg4DepH = Math.floor((leg3ArrMin + layover2Min) / 60) % 24
      const leg4 = makeLeg(origin, o.code, o.airline, o.alCode, ret, leg4DepH, o.dur, outPrice2)

      const legs = [leg1, leg2, leg3, leg4]
      const layovers: LayoverInfo[] = [
        { city: origin, duration_minutes: layover1Min, duration_display: fmtDur(layover1Min) },
        { city: origin, duration_minutes: layover2Min, duration_display: fmtDur(layover2Min) },
      ]

      const totalSingle = legs.reduce((s, l) => s + l.price, 0)
      const totalAll = totalSingle * pax
      const savings = directPrice - totalAll
      const outboundMin = o.dur + layover1Min + mainDur
      const returnMin = mainDur + layover2Min + o.dur

      return {
        outstation_city: o.code,
        outstation_city_name: o.name,
        legs, layovers,
        total_price: totalAll,
        direct_price: directPrice,
        savings: savings > 0 ? savings : null,
        savings_percent: savings > 0 ? Math.round(savings / directPrice * 1000) / 10 : null,
        total_transit_time_minutes: layover1Min + layover2Min,
        total_journey_hours: Math.round((outboundMin + returnMin) / 60 * 10) / 10,
        outbound_hours: Math.round(outboundMin / 60 * 10) / 10,
        return_hours: Math.round(returnMin / 60 * 10) / 10,
        currency: 'TWD',
      }
    })

  if (sort === 'price') results.sort((a, b) => a.total_price - b.total_price)
  else results.sort((a, b) => a.total_transit_time_minutes - b.total_transit_time_minutes)

  return { origin, destination: dest, results, direct_price: directPrice, result_count: results.length }
}

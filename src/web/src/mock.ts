export interface FlightLeg {
  origin: string; destination: string; airline: string;
  flight_number: string; departure_time: string; arrival_time: string; price: number;
}

export interface OutstationTicket {
  outstation_city: string; outstation_city_name: string;
  legs: FlightLeg[]; total_price: number;
  direct_price: number | null; savings: number | null;
  savings_percent: number | null; total_transit_time_minutes: number; currency: string;
}

export interface SearchResult {
  origin: string; destination: string; results: OutstationTicket[];
  direct_price: number | null; result_count: number;
}

const OUTSTATIONS = [
  { code: 'MFM', name: '澳門', base: 2200, airline: '虎航 IT' },
  { code: 'HKG', name: '香港', base: 2800, airline: '國泰 CX' },
  { code: 'ICN', name: '首爾仁川', base: 3200, airline: '大韓 KE' },
  { code: 'BKK', name: '曼谷', base: 3500, airline: '華航 CI' },
  { code: 'SIN', name: '新加坡', base: 4000, airline: '星宇 JX' },
  { code: 'KUL', name: '吉隆坡', base: 3300, airline: '亞航 AK' },
]

export function mockSearch(
  origin: string, dest: string, dep: string, ret: string, pax: number, sort: string,
): SearchResult {
  const directBase = 11000
  const directPrice = directBase * pax

  const results: OutstationTicket[] = OUTSTATIONS
    .filter(o => o.code !== origin && o.code !== dest)
    .map(o => {
      const legPrice = 3500 + Math.floor(Math.random() * 2500)
      const outPrice = o.base + Math.floor(Math.random() * 800)
      const total4 = outPrice + legPrice + legPrice + outPrice + Math.floor(Math.random() * 500)
      const totalAll = total4 * pax
      const savings = directPrice - totalAll
      return {
        outstation_city: o.code,
        outstation_city_name: o.name,
        legs: [
          { origin: o.code, destination: origin, airline: o.airline, flight_number: `${o.airline.split(' ')[1]}${100 + Math.floor(Math.random() * 900)}`, departure_time: `0${6 + Math.floor(Math.random() * 4)}:${['00','15','30','45'][Math.floor(Math.random()*4)]}`, arrival_time: `${10 + Math.floor(Math.random() * 3)}:${['00','15','30','45'][Math.floor(Math.random()*4)]}`, price: outPrice },
          { origin, destination: dest, airline: o.airline, flight_number: `${o.airline.split(' ')[1]}${100 + Math.floor(Math.random() * 900)}`, departure_time: `${12 + Math.floor(Math.random() * 3)}:${['00','15','30','45'][Math.floor(Math.random()*4)]}`, arrival_time: `${16 + Math.floor(Math.random() * 3)}:${['00','15','30','45'][Math.floor(Math.random()*4)]}`, price: legPrice },
          { origin: dest, destination: origin, airline: o.airline, flight_number: `${o.airline.split(' ')[1]}${100 + Math.floor(Math.random() * 900)}`, departure_time: `${17 + Math.floor(Math.random() * 3)}:${['00','15','30','45'][Math.floor(Math.random()*4)]}`, arrival_time: `${20 + Math.floor(Math.random() * 3)}:${['00','15','30','45'][Math.floor(Math.random()*4)]}`, price: legPrice + Math.floor(Math.random() * 500) },
          { origin, destination: o.code, airline: o.airline, flight_number: `${o.airline.split(' ')[1]}${100 + Math.floor(Math.random() * 900)}`, departure_time: `${21 + Math.floor(Math.random() * 2)}:${['00','15','30','45'][Math.floor(Math.random()*4)]}`, arrival_time: `${23}:${['00','30','45'][Math.floor(Math.random()*3)]}`, price: outPrice - Math.floor(Math.random() * 300) },
        ],
        total_price: totalAll,
        direct_price: directPrice,
        savings: savings > 0 ? savings : null,
        savings_percent: savings > 0 ? Math.round(savings / directPrice * 1000) / 10 : null,
        total_transit_time_minutes: 90 + Math.floor(Math.random() * 120),
        currency: 'TWD',
      }
    })

  if (sort === 'price') results.sort((a, b) => a.total_price - b.total_price)
  else results.sort((a, b) => a.total_transit_time_minutes - b.total_transit_time_minutes)

  return { origin, destination: dest, results, direct_price: directPrice, result_count: results.length }
}

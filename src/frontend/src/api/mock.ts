/**
 * Demo mode mock data — used when backend is not available (GitHub Pages).
 * Returns realistic outstation ticket data for demonstration.
 */
import type { TicketSearchResponse, OutstationTicket } from './tickets';

const MOCK_RESULTS: OutstationTicket[] = [
  {
    outstation_city: 'HKG',
    outstation_city_name: '香港',
    legs: [
      { origin: 'HKG', destination: 'TPE', airline: '國泰 CX', flight_number: 'CX530', departure_time: '08:30', arrival_time: '10:20', price: 2800 },
      { origin: 'TPE', destination: 'NRT', airline: '國泰 CX', flight_number: 'CX450', departure_time: '12:00', arrival_time: '16:15', price: 4200 },
      { origin: 'NRT', destination: 'TPE', airline: '國泰 CX', flight_number: 'CX451', departure_time: '17:30', arrival_time: '20:20', price: 4500 },
      { origin: 'TPE', destination: 'HKG', airline: '國泰 CX', flight_number: 'CX531', departure_time: '21:30', arrival_time: '23:30', price: 2600 },
    ],
    total_price: 14100,
    direct_price: 22000,
    savings: 7900,
    savings_percent: 35.9,
    total_transit_time_minutes: 100,
    currency: 'TWD',
  },
  {
    outstation_city: 'ICN',
    outstation_city_name: '首爾仁川',
    legs: [
      { origin: 'ICN', destination: 'TPE', airline: '大韓 KE', flight_number: 'KE691', departure_time: '09:00', arrival_time: '10:45', price: 3200 },
      { origin: 'TPE', destination: 'NRT', airline: '長榮 BR', flight_number: 'BR198', departure_time: '13:00', arrival_time: '17:00', price: 3800 },
      { origin: 'NRT', destination: 'TPE', airline: '長榮 BR', flight_number: 'BR197', departure_time: '18:30', arrival_time: '21:30', price: 4000 },
      { origin: 'TPE', destination: 'ICN', airline: '大韓 KE', flight_number: 'KE692', departure_time: '22:30', arrival_time: '02:00', price: 3000 },
    ],
    total_price: 14000,
    direct_price: 22000,
    savings: 8000,
    savings_percent: 36.4,
    total_transit_time_minutes: 135,
    currency: 'TWD',
  },
  {
    outstation_city: 'BKK',
    outstation_city_name: '曼谷',
    legs: [
      { origin: 'BKK', destination: 'TPE', airline: '華航 CI', flight_number: 'CI838', departure_time: '07:00', arrival_time: '11:30', price: 3500 },
      { origin: 'TPE', destination: 'NRT', airline: '華航 CI', flight_number: 'CI100', departure_time: '14:00', arrival_time: '18:10', price: 3600 },
      { origin: 'NRT', destination: 'TPE', airline: '華航 CI', flight_number: 'CI101', departure_time: '19:30', arrival_time: '22:20', price: 3800 },
      { origin: 'TPE', destination: 'BKK', airline: '華航 CI', flight_number: 'CI837', departure_time: '23:50', arrival_time: '03:00', price: 3300 },
    ],
    total_price: 14200,
    direct_price: 22000,
    savings: 7800,
    savings_percent: 35.5,
    total_transit_time_minutes: 150,
    currency: 'TWD',
  },
  {
    outstation_city: 'SIN',
    outstation_city_name: '新加坡',
    legs: [
      { origin: 'SIN', destination: 'TPE', airline: '星宇 JX', flight_number: 'JX722', departure_time: '06:30', arrival_time: '11:00', price: 4000 },
      { origin: 'TPE', destination: 'NRT', airline: '星宇 JX', flight_number: 'JX800', departure_time: '13:30', arrival_time: '17:40', price: 4100 },
      { origin: 'NRT', destination: 'TPE', airline: '星宇 JX', flight_number: 'JX801', departure_time: '19:00', arrival_time: '22:00', price: 4200 },
      { origin: 'TPE', destination: 'SIN', airline: '星宇 JX', flight_number: 'JX721', departure_time: '23:30', arrival_time: '04:30', price: 3800 },
    ],
    total_price: 16100,
    direct_price: 22000,
    savings: 5900,
    savings_percent: 26.8,
    total_transit_time_minutes: 150,
    currency: 'TWD',
  },
  {
    outstation_city: 'MFM',
    outstation_city_name: '澳門',
    legs: [
      { origin: 'MFM', destination: 'TPE', airline: '虎航 IT', flight_number: 'IT320', departure_time: '10:00', arrival_time: '11:50', price: 2200 },
      { origin: 'TPE', destination: 'NRT', airline: '虎航 IT', flight_number: 'IT200', departure_time: '14:30', arrival_time: '18:40', price: 3200 },
      { origin: 'NRT', destination: 'TPE', airline: '虎航 IT', flight_number: 'IT201', departure_time: '20:00', arrival_time: '23:00', price: 3400 },
      { origin: 'TPE', destination: 'MFM', airline: '虎航 IT', flight_number: 'IT321', departure_time: '08:00', arrival_time: '10:00', price: 2100 },
    ],
    total_price: 10900,
    direct_price: 22000,
    savings: 11100,
    savings_percent: 50.5,
    total_transit_time_minutes: 160,
    currency: 'TWD',
  },
];

export function mockSearchTickets(
  origin: string,
  destination: string,
  departureDate: string,
  returnDate: string,
  passengers: number,
  sortBy: string = 'price',
): TicketSearchResponse {
  // Simulate different results based on destination
  let results = MOCK_RESULTS.map(r => ({
    ...r,
    legs: r.legs.map((leg, i) => ({
      ...leg,
      origin: i === 1 ? origin : i === 2 ? destination : leg.origin,
      destination: i === 1 ? destination : i === 2 ? origin : leg.destination,
    })),
    total_price: r.total_price * passengers,
    direct_price: r.direct_price ? r.direct_price * passengers : null,
    savings: r.savings ? r.savings * passengers : null,
  }));

  // Filter out outstation = origin
  results = results.filter(r => r.outstation_city !== origin && r.outstation_city !== destination);

  // Sort
  if (sortBy === 'price') {
    results.sort((a, b) => a.total_price - b.total_price);
  } else if (sortBy === 'transit_time') {
    results.sort((a, b) => a.total_transit_time_minutes - b.total_transit_time_minutes);
  }

  return {
    origin,
    destination,
    departure_date: departureDate,
    return_date: returnDate,
    passengers,
    results,
    direct_price: 22000 * passengers,
    result_count: results.length,
    cached: false,
  };
}

/**
 * Ticket search API — US-1, US-2
 */
import { api } from './client';

export interface FlightLeg {
  origin: string;
  destination: string;
  airline: string;
  flight_number: string;
  departure_time: string;
  arrival_time: string;
  price: number;
}

export interface OutstationTicket {
  outstation_city: string;
  outstation_city_name: string;
  legs: FlightLeg[];
  total_price: number;
  direct_price: number | null;
  savings: number | null;
  savings_percent: number | null;
  total_transit_time_minutes: number;
  currency: string;
}

export interface TicketSearchRequest {
  origin: string;
  destination: string;
  departure_date: string;
  return_date: string;
  passengers: number;
  sort_by?: 'price' | 'transit_time' | 'airline';
  region_filter?: string;
}

export interface TicketSearchResponse {
  origin: string;
  destination: string;
  departure_date: string;
  return_date: string;
  passengers: number;
  results: OutstationTicket[];
  direct_price: number | null;
  result_count: number;
  cached: boolean;
}

export async function searchTickets(req: TicketSearchRequest) {
  return api.post<TicketSearchResponse>('/tickets/search', req);
}

import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "./client";

// --- Interfaces ---

export interface ClientRead {
  id: string;
  phone: string;
  name: string;
  created_at: string;
}

export interface MasterClientRead {
  client: ClientRead;
  first_visit_at: string | null;
  last_visit_at: string | null;
  visit_count: number;
}

export interface BookingRead {
  id: string;
  master_id: string;
  client_id: string;
  service_id: string;
  starts_at: string;
  ends_at: string;
  status: string;
  source_platform: string | null;
  notes: string | null;
  created_at: string;
  service_name: string | null;
  client_name: string | null;
  client_phone: string | null;
}

export interface ClientDetailRead {
  client: ClientRead;
  bookings: BookingRead[];
  visit_count: number;
}

// --- Hooks ---

export function useClients() {
  return useQuery<MasterClientRead[]>({
    queryKey: ["clients"],
    queryFn: () => apiRequest<MasterClientRead[]>("/clients"),
    staleTime: 30_000,
  });
}

export function useClientDetail(clientId: string) {
  return useQuery<ClientDetailRead>({
    queryKey: ["clients", clientId],
    queryFn: () => apiRequest<ClientDetailRead>(`/clients/${clientId}`),
    enabled: !!clientId,
  });
}

import { useQuery } from "@tanstack/react-query";
import { masterApiRequest } from "../stores/master-auth.ts";

export interface MasterClientRead {
  client: {
    id: string;
    phone: string;
    name: string;
  };
  first_visit_at: string;
  last_visit_at: string;
  visit_count: number;
}

export interface ClientDetailBooking {
  id: string;
  starts_at: string;
  ends_at: string;
  status: "confirmed" | "pending" | "cancelled" | "completed";
  service_name: string;
  client_name: string;
  client_phone: string;
}

export interface ClientDetailRead {
  client: {
    id: string;
    phone: string;
    name: string;
  };
  bookings: ClientDetailBooking[];
  visit_count: number;
  first_visit_at: string;
  last_visit_at: string;
}

export function useMasterClients() {
  return useQuery<MasterClientRead[]>({
    queryKey: ["master", "clients"],
    queryFn: () => masterApiRequest<MasterClientRead[]>("/clients"),
    staleTime: 60_000,
  });
}

export function useClientDetail(clientId: string | undefined) {
  return useQuery<ClientDetailRead>({
    queryKey: ["master", "clients", clientId],
    queryFn: () =>
      masterApiRequest<ClientDetailRead>(`/clients/${clientId}`),
    enabled: !!clientId,
    staleTime: 30_000,
  });
}

import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "./client.ts";
import { API } from "../lib/constants.ts";

export interface ServiceRead {
  id: string;
  master_id: string;
  name: string;
  description: string | null;
  duration_minutes: number;
  price: number;
  category: string | null;
  is_active: boolean;
  sort_order: number;
  created_at: string;
}

export function useServices(masterId: string | undefined) {
  return useQuery<ServiceRead[]>({
    queryKey: ["services", masterId],
    queryFn: () => apiRequest<ServiceRead[]>(API.MASTER_SERVICES(masterId!)),
    enabled: !!masterId,
    staleTime: 60_000,
  });
}

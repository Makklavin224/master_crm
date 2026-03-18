import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "./client";

// --- Interfaces ---

export interface PaymentRead {
  id: string;
  booking_id: string;
  amount: number; // in kopecks
  status: string; // pending, paid, cancelled, refunded
  payment_method: string | null;
  receipt_status: string; // not_applicable, pending, issued, failed, cancelled
  fiscalization_level: string | null;
  paid_at: string | null;
  created_at: string;
  payment_url: string | null;
  service_name: string | null;
  client_name: string | null;
}

export interface PaymentListResponse {
  items: PaymentRead[];
  total: number;
}

export interface PaymentFilters {
  status?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}

// --- Hooks ---

export function usePayments(filters: PaymentFilters = {}) {
  return useQuery<PaymentListResponse>({
    queryKey: ["payments", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters.status) params.set("status", filters.status);
      if (filters.date_from) params.set("date_from", filters.date_from);
      if (filters.date_to) params.set("date_to", filters.date_to);
      if (filters.limit !== undefined)
        params.set("limit", String(filters.limit));
      if (filters.offset !== undefined)
        params.set("offset", String(filters.offset));
      const qs = params.toString();
      return apiRequest<PaymentListResponse>(
        `/payments/history${qs ? `?${qs}` : ""}`,
      );
    },
    staleTime: 30_000,
  });
}

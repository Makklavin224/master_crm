import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "./client";
import { useAuth } from "../stores/auth";

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
  total_revenue: number; // sum of paid amounts in kopecks
}

export interface PaymentFilters {
  status?: string;
  date_from?: string;
  date_to?: string;
  payment_method?: string;
  limit?: number;
  offset?: number;
}

export interface CreateManualPaymentData {
  booking_id: string;
  payment_method: "cash" | "card_to_card" | "sbp";
  fiscalization_level?: "none" | "manual" | "auto" | null;
  amount_override?: number | null; // kopecks
}

export interface CreateRobokassaPaymentData {
  booking_id: string;
  fiscalization_level?: "none" | "manual" | "auto" | null;
  amount_override?: number | null; // kopecks
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
      if (filters.payment_method)
        params.set("payment_method", filters.payment_method);
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

export function useCreateManualPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateManualPaymentData) =>
      apiRequest<PaymentRead>("/payments/manual", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payments"] });
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
    },
  });
}

export function useCreateRobokassaPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateRobokassaPaymentData) =>
      apiRequest<PaymentRead>("/payments/robokassa", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payments"] });
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
    },
  });
}

export async function exportPaymentsCsv(
  filters: Omit<PaymentFilters, "limit" | "offset">,
) {
  const { token } = useAuth.getState();
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.payment_method)
    params.set("payment_method", filters.payment_method);
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  const qs = params.toString();
  const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";
  const res = await fetch(
    `${API_BASE}/payments/export-csv${qs ? `?${qs}` : ""}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!res.ok) throw new Error("Export failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `payments_${filters.date_from || "all"}_${filters.date_to || "all"}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { masterApiRequest } from "../stores/master-auth.ts";

// --- Interfaces ---

export interface PaymentRead {
  id: string;
  booking_id: string;
  amount: number;
  status: string;
  payment_method: string | null;
  receipt_status: string;
  fiscalization_level: string | null;
  paid_at: string | null;
  created_at: string;
  service_name: string;
  client_name: string;
  payment_url: string | null;
}

export interface PaymentRequisites {
  card_number: string | null;
  sbp_phone: string | null;
  bank_name: string | null;
  qr_code_base64: string;
}

export interface ManualReceiptData {
  amount_display: string;
  service_name: string;
  client_name: string;
  date: string;
}

export interface PaymentListResponse {
  items: PaymentRead[];
  total: number;
}

export interface RequisitesPaymentResponse {
  payment: PaymentRead;
  requisites: PaymentRequisites;
}

export interface PaymentHistoryFilters {
  status?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}

// --- Mutation hooks ---

export function useCreateManualPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      booking_id: string;
      payment_method: string;
      fiscalization_level?: string;
    }) =>
      masterApiRequest<PaymentRead>("/payments/manual", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payments", "history"] });
      queryClient.invalidateQueries({ queryKey: ["master", "bookings"] });
    },
  });
}

export function useCreateRobokassaPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      booking_id: string;
      fiscalization_level?: string;
    }) =>
      masterApiRequest<PaymentRead>("/payments/robokassa", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payments", "history"] });
      queryClient.invalidateQueries({ queryKey: ["master", "bookings"] });
    },
  });
}

export function useCreateRequisitesPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      booking_id: string;
      fiscalization_level?: string;
    }) =>
      masterApiRequest<RequisitesPaymentResponse>("/payments/requisites", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payments", "history"] });
      queryClient.invalidateQueries({ queryKey: ["master", "bookings"] });
    },
  });
}

export function useConfirmPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (paymentId: string) =>
      masterApiRequest<PaymentRead>(`/payments/${paymentId}/confirm`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payments", "history"] });
      queryClient.invalidateQueries({ queryKey: ["master", "bookings"] });
    },
  });
}

export function useCancelPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (paymentId: string) =>
      masterApiRequest<PaymentRead>(`/payments/${paymentId}/cancel`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payments", "history"] });
      queryClient.invalidateQueries({ queryKey: ["master", "bookings"] });
    },
  });
}

// --- Query hooks ---

export function usePaymentHistory(filters: PaymentHistoryFilters = {}) {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  if (filters.limit) params.set("limit", String(filters.limit));
  if (filters.offset) params.set("offset", String(filters.offset));
  const qs = params.toString();

  return useQuery<PaymentListResponse>({
    queryKey: ["payments", "history", filters],
    queryFn: () =>
      masterApiRequest<PaymentListResponse>(
        `/payments/history${qs ? `?${qs}` : ""}`,
      ),
    staleTime: 30_000,
  });
}

export function useReceiptData(paymentId: string | null) {
  return useQuery<ManualReceiptData>({
    queryKey: ["payments", "receipt", paymentId],
    queryFn: () =>
      masterApiRequest<ManualReceiptData>(
        `/payments/${paymentId}/receipt-data`,
      ),
    enabled: !!paymentId,
    staleTime: 60_000,
  });
}

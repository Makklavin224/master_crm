import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "./client";

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

export interface BookingListResponse {
  bookings: BookingRead[];
  total: number;
}

export interface BookingFilters {
  date_from?: string;
  date_to?: string;
  status?: string;
}

export interface ManualBookingCreate {
  service_id: string;
  starts_at: string;
  client_name: string;
  client_phone: string;
  notes?: string | null;
}

export function useBookings(filters: BookingFilters = {}) {
  const params = new URLSearchParams();
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  if (filters.status) params.set("status", filters.status);
  const qs = params.toString();

  return useQuery<BookingListResponse>({
    queryKey: ["bookings", filters],
    queryFn: () =>
      apiRequest<BookingListResponse>(`/bookings${qs ? `?${qs}` : ""}`),
    staleTime: 0,
  });
}

export function useCancelBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (bookingId: string) =>
      apiRequest<BookingRead>(`/bookings/${bookingId}/cancel`, {
        method: "PUT",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
    },
  });
}

export function useCreateManualBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ManualBookingCreate) =>
      apiRequest<BookingRead>("/bookings/manual", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
    },
  });
}

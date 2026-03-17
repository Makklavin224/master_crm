import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { masterApiRequest } from "../stores/master-auth.ts";

export interface MasterBookingRead {
  id: string;
  starts_at: string;
  ends_at: string;
  status: "confirmed" | "pending" | "cancelled" | "completed";
  service_name: string;
  client_name: string;
  client_phone: string;
}

export interface BookingListResponse {
  items: MasterBookingRead[];
  total: number;
}

export interface BookingFilters {
  date_from?: string;
  date_to?: string;
  status?: string;
}

export function useMasterBookings(filters: BookingFilters = {}) {
  const params = new URLSearchParams();
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  if (filters.status) params.set("status", filters.status);
  const qs = params.toString();

  return useQuery<BookingListResponse>({
    queryKey: ["master", "bookings", filters],
    queryFn: () =>
      masterApiRequest<BookingListResponse>(
        `/bookings${qs ? `?${qs}` : ""}`,
      ),
    staleTime: 30_000,
  });
}

export function useCancelBookingMaster() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (bookingId: string) =>
      masterApiRequest<MasterBookingRead>(`/bookings/${bookingId}/cancel`, {
        method: "PUT",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["master", "bookings"] });
    },
  });
}

export function useCreateManualBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      service_id: string;
      starts_at: string;
      client_name: string;
      client_phone: string;
    }) =>
      masterApiRequest<MasterBookingRead>("/bookings/manual", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["master", "bookings"] });
    },
  });
}

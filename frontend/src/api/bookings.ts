import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "./client.ts";
import { API } from "../lib/constants.ts";

export interface BookingCreate {
  master_id: string;
  service_id: string;
  starts_at: string; // ISO datetime
  client_name: string;
  client_phone: string;
  source_platform: string;
  tg_user_id?: string;
}

export interface BookingRead {
  id: string;
  master_id: string;
  client_id: string | null;
  service_id: string;
  starts_at: string;
  ends_at: string;
  status: "confirmed" | "pending" | "cancelled" | "completed";
  source_platform: string;
  notes: string | null;
  created_at: string;
  service_name: string;
  client_name: string;
  client_phone: string;
}

export function useCreateBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { booking: BookingCreate; initDataRaw?: string | null }) =>
      apiRequest<BookingRead>(
        API.BOOKINGS,
        {
          method: "POST",
          body: JSON.stringify(data.booking),
        },
        data.initDataRaw,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
    },
  });
}

export function useMyBookings(tgUserId: string | null, initDataRaw: string | null) {
  return useQuery<BookingRead[]>({
    queryKey: ["bookings", "my", tgUserId],
    queryFn: () =>
      apiRequest<BookingRead[]>(
        `${API.BOOKINGS}?tg_user_id=${tgUserId}`,
        {},
        initDataRaw,
      ),
    enabled: !!tgUserId && !!initDataRaw,
    staleTime: 30_000,
  });
}

export function useCancelBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { bookingId: string; initDataRaw?: string | null }) =>
      apiRequest<BookingRead>(
        API.BOOKING_CANCEL(data.bookingId),
        { method: "PUT" },
        data.initDataRaw,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
    },
  });
}

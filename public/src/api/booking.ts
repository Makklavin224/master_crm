import { useMutation } from "@tanstack/react-query";
import { apiRequest } from "./client.ts";
import type { BookingCreate, BookingRead } from "./types.ts";

export function useCreateBooking() {
  return useMutation({
    mutationFn: (data: BookingCreate) =>
      apiRequest<BookingRead>("/bookings", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  });
}

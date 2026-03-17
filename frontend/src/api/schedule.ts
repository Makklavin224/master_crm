import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "./client.ts";
import { API } from "../lib/constants.ts";

export interface AvailableSlot {
  time: string; // "HH:MM"
}

export interface AvailableSlotsResponse {
  date: string;
  slots: AvailableSlot[];
}

export function useAvailableSlots(
  masterId: string | undefined,
  date: string | null,
  serviceId: string | null,
) {
  return useQuery<AvailableSlotsResponse>({
    queryKey: ["slots", masterId, date, serviceId],
    queryFn: () =>
      apiRequest<AvailableSlotsResponse>(
        `${API.MASTER_SLOTS(masterId!)}?date=${date}&service_id=${serviceId}`,
      ),
    enabled: !!masterId && !!date && !!serviceId,
    staleTime: 0, // Always refetch -- slots can be booked by others
  });
}

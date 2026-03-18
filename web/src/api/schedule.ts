import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "./client";

export interface ScheduleDayRead {
  day_of_week: number;
  start_time: string | null;
  end_time: string | null;
  break_start: string | null;
  break_end: string | null;
  is_working: boolean;
}

export interface ScheduleExceptionRead {
  id: string;
  exception_date: string;
  is_day_off: boolean;
  start_time: string | null;
  end_time: string | null;
  reason: string | null;
  created_at: string;
}

export function useScheduleTemplate() {
  return useQuery<ScheduleDayRead[]>({
    queryKey: ["schedule", "template"],
    queryFn: () => apiRequest<ScheduleDayRead[]>("/schedule"),
    staleTime: 60_000,
  });
}

export function useScheduleExceptions(month?: string) {
  const params = new URLSearchParams();
  if (month) params.set("month", month);
  const qs = params.toString();

  return useQuery<ScheduleExceptionRead[]>({
    queryKey: ["schedule", "exceptions", month],
    queryFn: () =>
      apiRequest<ScheduleExceptionRead[]>(
        `/schedule/exceptions${qs ? `?${qs}` : ""}`,
      ),
    staleTime: 60_000,
  });
}

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { masterApiRequest } from "../stores/master-auth.ts";

export interface ScheduleDayRead {
  day_of_week: number; // 0=Mon .. 6=Sun
  start_time: string | null; // "HH:MM"
  end_time: string | null;
  break_start: string | null;
  break_end: string | null;
  is_working: boolean;
}

export interface ScheduleTemplate {
  days: ScheduleDayRead[];
}

export interface ScheduleExceptionRead {
  id: string;
  exception_date: string; // "YYYY-MM-DD"
  is_day_off: boolean;
  start_time: string | null;
  end_time: string | null;
  reason: string | null;
}

export interface ScheduleExceptionCreate {
  exception_date: string;
  is_day_off: boolean;
  start_time?: string | null;
  end_time?: string | null;
  reason?: string | null;
}

export function useMasterSchedule() {
  return useQuery<ScheduleDayRead[]>({
    queryKey: ["master", "schedule"],
    queryFn: () => masterApiRequest<ScheduleDayRead[]>("/schedule"),
    staleTime: 60_000,
  });
}

export function useUpdateSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ScheduleTemplate) =>
      masterApiRequest<ScheduleDayRead[]>("/schedule", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["master", "schedule"] });
    },
  });
}

export function useScheduleExceptions() {
  return useQuery<ScheduleExceptionRead[]>({
    queryKey: ["master", "schedule", "exceptions"],
    queryFn: () =>
      masterApiRequest<ScheduleExceptionRead[]>("/schedule/exceptions"),
    staleTime: 60_000,
  });
}

export function useCreateException() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ScheduleExceptionCreate) =>
      masterApiRequest<ScheduleExceptionRead>("/schedule/exceptions", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["master", "schedule", "exceptions"],
      });
    },
  });
}

export function useDeleteException() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      masterApiRequest<void>(`/schedule/exceptions/${id}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["master", "schedule", "exceptions"],
      });
    },
  });
}

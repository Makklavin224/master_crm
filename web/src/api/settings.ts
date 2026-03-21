import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "./client";

// --- Interfaces ---

export interface MasterSettings {
  buffer_minutes: number;
  cancellation_deadline_hours: number;
  slot_interval_minutes: number;
}

export interface MasterSettingsUpdate {
  buffer_minutes?: number;
  cancellation_deadline_hours?: number;
  slot_interval_minutes?: number;
}

export interface NotificationSettings {
  reminders_enabled: boolean;
  reminder_1_hours: number;
  reminder_2_hours: number | null;
  address_note: string | null;
}

export interface NotificationSettingsUpdate {
  reminders_enabled?: boolean;
  reminder_1_hours?: number;
  reminder_2_hours?: number | null;
  address_note?: string | null;
}

export interface PaymentSettings {
  card_number: string | null;
  sbp_phone: string | null;
  bank_name: string | null;
  has_robokassa: boolean;
  robokassa_is_test: boolean;
  fiscalization_level: string;
  has_seen_grey_warning: boolean;
  receipt_sno: string;
  inn: string | null;
  fns_connected: boolean;
}

export interface PaymentSettingsUpdate {
  card_number?: string | null;
  sbp_phone?: string | null;
  bank_name?: string | null;
  fiscalization_level?: string;
  receipt_sno?: string;
  has_seen_grey_warning?: boolean;
}

export interface ScheduleDayEntry {
  day_of_week: number;
  start_time: string;
  end_time: string;
  break_start: string | null;
  break_end: string | null;
  is_working: boolean;
}

export interface ScheduleTemplate {
  days: ScheduleDayEntry[];
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

export interface ScheduleExceptionCreate {
  exception_date: string;
  is_day_off?: boolean;
  start_time?: string | null;
  end_time?: string | null;
  reason?: string | null;
}

// --- Profile settings ---

export interface ProfileSettings {
  name: string;
  username: string | null;
  specialization: string | null;
  city: string | null;
  avatar_path: string | null;
  instagram_url: string | null;
}

export function useProfileSettings() {
  return useQuery<ProfileSettings>({
    queryKey: ["settings", "profile"],
    queryFn: () => apiRequest<ProfileSettings>("/settings/profile"),
    staleTime: 60_000,
  });
}

// --- Settings hooks ---

export function useSettings() {
  return useQuery<MasterSettings>({
    queryKey: ["settings"],
    queryFn: () => apiRequest<MasterSettings>("/settings"),
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: MasterSettingsUpdate) =>
      apiRequest<MasterSettings>("/settings", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings"] }),
  });
}

// --- Notification settings hooks ---

export function useNotificationSettings() {
  return useQuery<NotificationSettings>({
    queryKey: ["notification-settings"],
    queryFn: () =>
      apiRequest<NotificationSettings>("/settings/notifications"),
  });
}

export function useUpdateNotificationSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: NotificationSettingsUpdate) =>
      apiRequest<NotificationSettings>("/settings/notifications", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["notification-settings"] }),
  });
}

// --- Payment settings hooks ---

export function usePaymentSettings() {
  return useQuery<PaymentSettings>({
    queryKey: ["payment-settings"],
    queryFn: () => apiRequest<PaymentSettings>("/settings/payment"),
  });
}

export function useUpdatePaymentSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: PaymentSettingsUpdate) =>
      apiRequest<PaymentSettings>("/settings/payment", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["payment-settings"] }),
  });
}

export function useBindInn() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (inn: string) =>
      apiRequest<PaymentSettings>("/settings/payment/inn", {
        method: "POST",
        body: JSON.stringify({ inn }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payment-settings"] }),
  });
}

export function useUnbindInn() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiRequest<PaymentSettings>("/settings/payment/inn", {
        method: "DELETE",
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payment-settings"] }),
  });
}

// --- Schedule template hooks ---

export function useScheduleTemplate() {
  return useQuery<ScheduleDayEntry[]>({
    queryKey: ["schedule-template"],
    queryFn: () => apiRequest<ScheduleDayEntry[]>("/schedule/template"),
  });
}

export function useUpdateScheduleTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ScheduleTemplate) =>
      apiRequest("/schedule/template", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["schedule-template"] }),
  });
}

// --- Schedule exceptions hooks ---

export function useScheduleExceptions() {
  return useQuery<ScheduleExceptionRead[]>({
    queryKey: ["schedule-exceptions"],
    queryFn: () =>
      apiRequest<ScheduleExceptionRead[]>("/schedule/exceptions"),
  });
}

export function useCreateScheduleException() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ScheduleExceptionCreate) =>
      apiRequest<ScheduleExceptionRead>("/schedule/exceptions", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["schedule-exceptions"] }),
  });
}

export function useDeleteScheduleException() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiRequest<void>(`/schedule/exceptions/${id}`, { method: "DELETE" }),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["schedule-exceptions"] }),
  });
}

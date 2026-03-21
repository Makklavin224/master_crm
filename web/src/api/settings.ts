import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest, ApiError } from "./client";
import { useAuth } from "../stores/auth";

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

export interface ProfileSettingsUpdate {
  name?: string;
  username?: string | null;
  specialization?: string | null;
  city?: string | null;
  instagram_url?: string | null;
}

export function useProfileSettings() {
  return useQuery<ProfileSettings>({
    queryKey: ["settings", "profile"],
    queryFn: () => apiRequest<ProfileSettings>("/settings/profile"),
    staleTime: 60_000,
  });
}

export function useUpdateProfileSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ProfileSettingsUpdate) =>
      apiRequest<ProfileSettings>("/settings/profile", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["settings", "profile"] });
      qc.invalidateQueries({ queryKey: ["auth"] });
    },
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

export interface RobokassaSetupData {
  merchant_login: string;
  password1: string;
  password2: string;
  is_test: boolean;
  hash_algorithm: string;
}

export function useSetupRobokassa() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: RobokassaSetupData) =>
      apiRequest<PaymentSettings>("/settings/payment/robokassa", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payment-settings"] }),
  });
}

export function useDisconnectRobokassa() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiRequest<PaymentSettings>("/settings/payment/robokassa", {
        method: "DELETE",
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payment-settings"] }),
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

// --- Platform status hooks ---

export interface PlatformStatusResponse {
  tg_linked: boolean;
  max_linked: boolean;
  vk_linked: boolean;
  tg_user_id: string | null;
  max_user_id: string | null;
  vk_user_id: string | null;
}

export function usePlatformStatus() {
  return useQuery<PlatformStatusResponse>({
    queryKey: ["platform-status"],
    queryFn: () => apiRequest<PlatformStatusResponse>("/settings/platforms"),
    staleTime: 60_000,
  });
}

export function useUnlinkPlatform() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (platform: string) =>
      apiRequest<{ ok: boolean; platform: string }>(`/settings/platforms/${platform}`, {
        method: "DELETE",
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["platform-status"] }),
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

// --- Portfolio ---

export interface PortfolioPhoto {
  id: string;
  file_path: string;
  thumbnail_path: string;
  caption: string | null;
  service_tag: string | null;
  sort_order: number;
  created_at: string;
}

export function usePortfolio() {
  return useQuery<PortfolioPhoto[]>({
    queryKey: ["portfolio"],
    queryFn: () => apiRequest<PortfolioPhoto[]>("/portfolio/"),
  });
}

export function useUploadPhoto() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { file: File; serviceTag?: string; caption?: string }) => {
      const formData = new FormData();
      formData.append("file", data.file);
      if (data.serviceTag) formData.append("service_tag", data.serviceTag);
      if (data.caption) formData.append("caption", data.caption);

      const { token } = useAuth.getState();
      const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";
      const res = await fetch(`${API_BASE}/portfolio/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Ошибка загрузки" }));
        throw new ApiError(res.status, err.detail);
      }
      return res.json() as Promise<PortfolioPhoto>;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
  });
}

export function useDeletePhoto() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (photoId: string) =>
      apiRequest<void>(`/portfolio/${photoId}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
  });
}

export function useUpdatePhoto() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; caption?: string; service_tag?: string | null }) =>
      apiRequest<PortfolioPhoto>(`/portfolio/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
  });
}

export function useReorderPhotos() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (items: { id: string; sort_order: number }[]) =>
      apiRequest<void>("/portfolio/reorder", {
        method: "PUT",
        body: JSON.stringify({ items }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
  });
}

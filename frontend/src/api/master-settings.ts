import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { masterApiRequest, useMasterAuth } from "../stores/master-auth.ts";
import { ApiError } from "./client.ts";

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

export function useMasterSettings() {
  return useQuery<MasterSettings>({
    queryKey: ["master", "settings"],
    queryFn: () => masterApiRequest<MasterSettings>("/settings"),
    staleTime: 60_000,
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: MasterSettingsUpdate) =>
      masterApiRequest<MasterSettings>("/settings", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["master", "settings"] });
    },
  });
}

// --- Notification settings ---

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

export function useNotificationSettings() {
  return useQuery<NotificationSettings>({
    queryKey: ["master", "notificationSettings"],
    queryFn: () =>
      masterApiRequest<NotificationSettings>("/settings/notifications"),
    staleTime: 60_000,
  });
}

export function useUpdateNotificationSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: NotificationSettingsUpdate) =>
      masterApiRequest<NotificationSettings>("/settings/notifications", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["master", "notificationSettings"],
      });
    },
  });
}

// --- Payment settings ---

export interface PaymentSettings {
  card_number: string | null;
  sbp_phone: string | null;
  bank_name: string | null;
  has_robokassa: boolean;
  robokassa_is_test: boolean;
  robokassa_hash_algorithm: string;
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
}

export interface RobokassaSetup {
  merchant_login: string;
  password1: string;
  password2: string;
  is_test: boolean;
  hash_algorithm: string;
}

export function usePaymentSettings() {
  return useQuery<PaymentSettings>({
    queryKey: ["master", "paymentSettings"],
    queryFn: () =>
      masterApiRequest<PaymentSettings>("/settings/payment"),
    staleTime: 60_000,
  });
}

export function useUpdatePaymentSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PaymentSettingsUpdate) =>
      masterApiRequest<PaymentSettings>("/settings/payment", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["master", "paymentSettings"],
      });
    },
  });
}

export function useSetupRobokassa() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: RobokassaSetup) =>
      masterApiRequest<PaymentSettings>("/settings/payment/robokassa", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["master", "paymentSettings"],
      });
    },
  });
}

export function useDisconnectRobokassa() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      masterApiRequest<PaymentSettings>("/settings/payment/robokassa", {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["master", "paymentSettings"],
      });
    },
  });
}

export function useMarkGreyWarningSeen() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      masterApiRequest<undefined>("/settings/payment/grey-warning-seen", {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["master", "paymentSettings"],
      });
    },
  });
}

export function useBindInn() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (inn: string) =>
      masterApiRequest<PaymentSettings>("/settings/payment/inn", {
        method: "POST",
        body: JSON.stringify({ inn }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["master", "paymentSettings"],
      });
    },
  });
}

export function useUnbindInn() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      masterApiRequest<PaymentSettings>("/settings/payment/inn", {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["master", "paymentSettings"],
      });
    },
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
    queryKey: ["master", "portfolio"],
    queryFn: () => masterApiRequest<PortfolioPhoto[]>("/portfolio/"),
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

      const { token } = useMasterAuth.getState();
      const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE}/portfolio/upload`, {
        method: "POST",
        headers,
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Ошибка загрузки" }));
        throw new ApiError(res.status, err.detail);
      }
      return res.json() as Promise<PortfolioPhoto>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["master", "portfolio"] });
    },
  });
}

export function useDeletePhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (photoId: string) =>
      masterApiRequest<void>(`/portfolio/${photoId}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["master", "portfolio"] });
    },
  });
}

export function useUpdatePhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; caption?: string; service_tag?: string | null }) =>
      masterApiRequest<PortfolioPhoto>(`/portfolio/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["master", "portfolio"] });
    },
  });
}

export function useReorderPhotos() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (items: { id: string; sort_order: number }[]) =>
      masterApiRequest<void>("/portfolio/reorder", {
        method: "PUT",
        body: JSON.stringify({ items }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["master", "portfolio"] });
    },
  });
}

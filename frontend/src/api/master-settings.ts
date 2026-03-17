import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { masterApiRequest } from "../stores/master-auth.ts";

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

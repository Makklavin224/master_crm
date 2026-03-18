import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "./client";

export interface ServiceRead {
  id: string;
  master_id: string;
  name: string;
  description: string | null;
  duration_minutes: number;
  price: number;
  category: string | null;
  is_active: boolean;
  sort_order: number;
  created_at: string;
}

export interface ServiceCreate {
  name: string;
  duration_minutes: number;
  price: number;
  category?: string | null;
  description?: string | null;
}

export interface ServiceUpdate {
  name?: string;
  duration_minutes?: number;
  price?: number;
  category?: string | null;
  description?: string | null;
  is_active?: boolean;
  sort_order?: number;
}

export function useServices() {
  return useQuery<ServiceRead[]>({
    queryKey: ["services"],
    queryFn: () => apiRequest<ServiceRead[]>("/services"),
    staleTime: 60_000,
  });
}

export function useCreateService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ServiceCreate) =>
      apiRequest<ServiceRead>("/services", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["services"] });
    },
  });
}

export function useUpdateService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ServiceUpdate }) =>
      apiRequest<ServiceRead>(`/services/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["services"] });
    },
  });
}

export function useDeleteService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      apiRequest<void>(`/services/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["services"] });
    },
  });
}

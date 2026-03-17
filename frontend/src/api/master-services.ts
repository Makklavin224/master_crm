import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { masterApiRequest } from "../stores/master-auth.ts";

export interface MasterServiceRead {
  id: string;
  name: string;
  description: string | null;
  duration_minutes: number;
  price: number;
  category: string | null;
  is_active: boolean;
  sort_order: number;
}

export interface ServiceCreate {
  name: string;
  description?: string | null;
  duration_minutes: number;
  price: number;
  category?: string | null;
}

export interface ServiceUpdate {
  name?: string;
  description?: string | null;
  duration_minutes?: number;
  price?: number;
  category?: string | null;
  is_active?: boolean;
  sort_order?: number;
}

export function useMasterServices() {
  return useQuery<MasterServiceRead[]>({
    queryKey: ["master", "services"],
    queryFn: () => masterApiRequest<MasterServiceRead[]>("/services"),
    staleTime: 60_000,
  });
}

export function useCreateService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ServiceCreate) =>
      masterApiRequest<MasterServiceRead>("/services", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["master", "services"] });
    },
  });
}

export function useUpdateService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ServiceUpdate }) =>
      masterApiRequest<MasterServiceRead>(`/services/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["master", "services"] });
    },
  });
}

export function useDeleteService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      masterApiRequest<void>(`/services/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["master", "services"] });
    },
  });
}

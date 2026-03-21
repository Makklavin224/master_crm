import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "./client.ts";
import type {
  MasterProfile,
  ServiceRead,
  AvailableSlotsResponse,
  ReviewRead,
  PortfolioPhoto,
} from "./types.ts";

export function useMasterProfile(username: string) {
  return useQuery<MasterProfile>({
    queryKey: ["masterProfile", username],
    queryFn: () => apiRequest<MasterProfile>(`/masters/${username}/profile`),
    enabled: !!username,
    staleTime: 60_000,
  });
}

export function useMasterServices(username: string) {
  return useQuery<ServiceRead[]>({
    queryKey: ["masterServices", username],
    queryFn: () => apiRequest<ServiceRead[]>(`/masters/${username}/services`),
    enabled: !!username,
    staleTime: 60_000,
  });
}

export function useMasterSlots(
  username: string,
  date: string,
  serviceId: string,
) {
  return useQuery<AvailableSlotsResponse>({
    queryKey: ["masterSlots", username, date, serviceId],
    queryFn: () =>
      apiRequest<AvailableSlotsResponse>(
        `/masters/${username}/slots?date=${date}&service_id=${serviceId}`,
      ),
    enabled: !!username && !!date && !!serviceId,
    staleTime: 30_000,
  });
}

export function useMasterReviews(username: string) {
  return useQuery<ReviewRead[]>({
    queryKey: ["masterReviews", username],
    queryFn: () => apiRequest<ReviewRead[]>(`/masters/${username}/reviews`),
    enabled: !!username,
    staleTime: 120_000,
  });
}

export function useMasterPortfolio(username: string) {
  return useQuery<PortfolioPhoto[]>({
    queryKey: ["masterPortfolio", username],
    queryFn: () =>
      apiRequest<PortfolioPhoto[]>(`/masters/${username}/portfolio`),
    enabled: !!username,
    staleTime: 120_000,
  });
}

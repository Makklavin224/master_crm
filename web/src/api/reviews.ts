import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "./client";

// --- Interfaces ---

export interface ReviewAdminRead {
  id: string;
  booking_id: string | null;
  rating: number;
  text: string | null;
  client_name: string;
  client_phone: string;
  service_name: string;
  master_reply: string | null;
  master_replied_at: string | null;
  status: string; // published, pending_reply
  created_at: string;
}

export interface ReviewsListResponse {
  reviews: ReviewAdminRead[];
  total: number;
}

export interface ReviewFilters {
  status?: string;
  page?: number;
  page_size?: number;
}

// --- Hooks ---

export function useReviews(filters: ReviewFilters = {}) {
  return useQuery<ReviewsListResponse>({
    queryKey: ["reviews", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters.status && filters.status !== "all")
        params.set("status", filters.status);
      if (filters.page !== undefined) params.set("page", String(filters.page));
      if (filters.page_size !== undefined)
        params.set("page_size", String(filters.page_size));
      const qs = params.toString();
      return apiRequest<ReviewsListResponse>(
        `/reviews${qs ? `?${qs}` : ""}`,
      );
    },
    staleTime: 30_000,
  });
}

export function useReplyToReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      reviewId,
      reply_text,
    }: {
      reviewId: string;
      reply_text: string;
    }) =>
      apiRequest<ReviewAdminRead>(`/reviews/${reviewId}/reply`, {
        method: "PUT",
        body: JSON.stringify({ reply_text }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews"] });
    },
  });
}

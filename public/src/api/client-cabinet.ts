import { apiRequest } from "./client.ts";
import type {
  OTPResponse,
  SessionResponse,
  ClientBookingsResponse,
  ReviewCreateRequest,
  ReviewCreateResponse,
} from "./types.ts";

export async function requestOTP(phone: string): Promise<OTPResponse> {
  return apiRequest<OTPResponse>("/client/auth/request-code", {
    method: "POST",
    body: JSON.stringify({ phone }),
    credentials: "include",
  });
}

export async function verifyOTP(
  phone: string,
  code: string,
): Promise<SessionResponse> {
  const result = await apiRequest<SessionResponse>("/client/auth/verify-code", {
    method: "POST",
    body: JSON.stringify({ phone, code }),
    credentials: "include",
  });
  // Store token for Bearer fallback when cookies don't work
  if (result.token) {
    localStorage.setItem("client_token", result.token);
  }
  return result;
}

export async function getClientBookings(): Promise<ClientBookingsResponse> {
  return apiRequest<ClientBookingsResponse>("/client/bookings", {
    credentials: "include",
  });
}

export async function createReview(
  data: ReviewCreateRequest,
): Promise<ReviewCreateResponse> {
  return apiRequest<ReviewCreateResponse>("/client/reviews", {
    method: "POST",
    body: JSON.stringify(data),
    credentials: "include",
  });
}

export async function cancelBooking(
  bookingId: string,
  reason?: string,
): Promise<void> {
  await apiRequest<unknown>(`/bookings/${bookingId}/cancel`, {
    method: "PUT",
    body: JSON.stringify({ reason: reason || "" }),
    credentials: "include",
  });
}

export async function rescheduleBooking(
  bookingId: string,
  newStartsAt: string,
): Promise<void> {
  await apiRequest<unknown>(`/bookings/${bookingId}/reschedule`, {
    method: "PUT",
    body: JSON.stringify({ new_starts_at: newStartsAt }),
    credentials: "include",
  });
}

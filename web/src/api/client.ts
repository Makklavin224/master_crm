import { useAuth } from "../stores/auth";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30_000);

  try {
    const { token } = useAuth.getState();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const signal =
      options.signal && typeof AbortSignal.any === "function"
        ? AbortSignal.any([options.signal, controller.signal])
        : controller.signal;

    const res = await fetch(`${API_BASE}${path}`, { ...options, headers, signal });
    if (!res.ok) {
      const err = await res
        .json()
        .catch(() => ({ detail: "Ошибка сети" }));
      if (res.status === 401) {
        useAuth.getState().logout();
      }
      throw new ApiError(res.status, err.detail || `HTTP ${res.status}`);
    }

    if (res.status === 204) return undefined as T;
    return res.json();
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError(0, "Превышено время ожидания. Попробуйте позже.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

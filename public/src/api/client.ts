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
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    // Add Bearer token from localStorage if available (fallback when cookies fail)
    const token = localStorage.getItem("client_token");
    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const signal =
      options.signal && typeof AbortSignal.any === "function"
        ? AbortSignal.any([options.signal, controller.signal])
        : controller.signal;

    const response = await fetch(`${API_BASE}${path}`, { ...options, headers, signal });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Ошибка сети" }));
      throw new ApiError(response.status, error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError(0, "Превышено время ожидания. Попробуйте позже.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

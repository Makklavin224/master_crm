import { create } from "zustand";
import { ApiError } from "../api/client.ts";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

interface MasterAuthState {
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (initDataRaw: string) => Promise<boolean>;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useMasterAuth = create<MasterAuthState>((set) => ({
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (initDataRaw: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/auth/tg`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ init_data: initDataRaw }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: "Auth error" }));
        if (response.status === 401 || response.status === 404) {
          set({ isLoading: false, isAuthenticated: false, error: err.detail });
          return false;
        }
        throw new ApiError(response.status, err.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      set({
        token: data.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      return true;
    } catch (e) {
      const message = e instanceof Error ? e.message : "Auth failed";
      set({ isLoading: false, isAuthenticated: false, error: message });
      return false;
    }
  },

  setToken: (token) =>
    set({ token, isAuthenticated: !!token }),

  logout: () =>
    set({ token: null, isAuthenticated: false, error: null }),
}));

/**
 * Make an authenticated API request using the master's JWT token.
 * Attaches Bearer token from master-auth store to Authorization header.
 */
export async function masterApiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const { token } = useMasterAuth.getState();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Network error" }));
    throw new ApiError(response.status, error.detail || `HTTP ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

import { create } from "zustand";
import { ApiError } from "../api/client.ts";
import type { PlatformBridge } from "../platform/types.ts";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";
const TOKEN_KEY = "master_token";

function safeGetItem(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeSetItem(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Ignore storage errors
  }
}

function safeRemoveItem(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch {
    // Ignore storage errors
  }
}

export type MasterRole = "master" | "client" | "detecting";

interface MasterAuthState {
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  role: MasterRole;

  login: (initDataRaw: string) => Promise<boolean>;
  setToken: (token: string | null) => void;
  logout: () => void;
  hydrate: () => void;
  setRole: (role: "master" | "client") => void;
  autoDetectRole: (bridge: PlatformBridge) => Promise<void>;
}

/** Map platform to its auth endpoint and request body key */
function getAuthConfig(platform: string, initDataRaw: string): { endpoint: string; body: Record<string, string> } | null {
  switch (platform) {
    case "telegram":
      return { endpoint: "/auth/tg", body: { init_data: initDataRaw } };
    case "max":
      return { endpoint: "/auth/max", body: { init_data: initDataRaw } };
    case "vk":
      return { endpoint: "/auth/vk", body: { launch_params: initDataRaw } };
    default:
      return null;
  }
}

export const useMasterAuth = create<MasterAuthState>((set, get) => ({
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  role: "detecting" as MasterRole,

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
      safeSetItem(TOKEN_KEY, data.access_token);
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

  setToken: (token) => {
    if (token) {
      safeSetItem(TOKEN_KEY, token);
    } else {
      safeRemoveItem(TOKEN_KEY);
    }
    set({ token, isAuthenticated: !!token });
  },

  logout: () => {
    safeRemoveItem(TOKEN_KEY);
    set({ token: null, isAuthenticated: false, error: null });
  },

  hydrate: () => {
    const token = safeGetItem(TOKEN_KEY);
    if (token) {
      set({ token, isAuthenticated: true });
    }
  },

  setRole: (role: "master" | "client") => {
    set({ role });
  },

  autoDetectRole: async (bridge: PlatformBridge) => {
    set({ role: "detecting", isLoading: true });

    // 1. Check localStorage for existing token
    const existingToken = safeGetItem(TOKEN_KEY);
    if (existingToken) {
      set({ token: existingToken, isAuthenticated: true, role: "master", isLoading: false });
      return;
    }

    // 2. Get init data from platform bridge
    const initDataRaw = bridge.getInitDataRaw();
    if (!initDataRaw) {
      // Web platform or no init data -- treat as client
      set({ role: "client", isAuthenticated: false, isLoading: false });
      return;
    }

    // 3. Determine auth endpoint based on platform
    const authConfig = getAuthConfig(bridge.platform, initDataRaw);
    if (!authConfig) {
      set({ role: "client", isAuthenticated: false, isLoading: false });
      return;
    }

    // 4. Try to authenticate
    try {
      const response = await fetch(`${API_BASE}${authConfig.endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(authConfig.body),
      });

      if (response.ok) {
        const data = await response.json();
        safeSetItem(TOKEN_KEY, data.access_token);
        set({
          token: data.access_token,
          isAuthenticated: true,
          role: "master",
          isLoading: false,
          error: null,
        });
        return;
      }

      // 401/404 = not a master, this is normal
      if (response.status === 401 || response.status === 404) {
        set({ role: "client", isAuthenticated: false, isLoading: false });
        return;
      }

      // Other errors -- default to client
      set({ role: "client", isAuthenticated: false, isLoading: false });
    } catch {
      // Network error -- default to client
      set({ role: "client", isAuthenticated: false, isLoading: false });
    }
  },
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

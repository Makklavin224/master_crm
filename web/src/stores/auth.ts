import { create } from "zustand";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";
const TOKEN_KEY = "admin_token";

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

export interface MasterProfile {
  id: string;
  email: string | null;
  phone: string | null;
  name: string;
  business_name: string | null;
  timezone: string;
  is_active: boolean;
  created_at: string;
}

interface AuthState {
  token: string | null;
  profile: MasterProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  loginEmail: (email: string, password: string) => Promise<boolean>;
  setToken: (token: string) => void;
  logout: () => void;
  hydrate: () => void;
  fetchProfile: () => Promise<void>;
}

export const useAuth = create<AuthState>((set, get) => ({
  token: null,
  profile: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  fetchProfile: async () => {
    const { token } = get();
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const profile: MasterProfile = await res.json();
        set({ profile });
      }
    } catch {
      // Silent fail -- profile is non-critical
    }
  },

  loginEmail: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Login failed" }));
        set({ isLoading: false, error: err.detail });
        return false;
      }
      const { access_token } = await res.json();
      safeSetItem(TOKEN_KEY, access_token);
      set({ token: access_token, isAuthenticated: true, isLoading: false });
      // Fetch profile after login
      get().fetchProfile();
      return true;
    } catch {
      set({ isLoading: false, error: "Network error" });
      return false;
    }
  },

  setToken: (token) => {
    safeSetItem(TOKEN_KEY, token);
    set({ token, isAuthenticated: true, error: null });
    // Fetch profile after setting token (magic link flow)
    get().fetchProfile();
  },

  logout: () => {
    safeRemoveItem(TOKEN_KEY);
    set({ token: null, profile: null, isAuthenticated: false });
  },

  hydrate: () => {
    const token = safeGetItem(TOKEN_KEY);
    if (token) {
      set({ token, isAuthenticated: true });
      // Fetch profile on hydrate
      get().fetchProfile();
    }
  },
}));

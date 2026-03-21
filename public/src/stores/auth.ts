import { create } from "zustand";
import { apiRequest } from "../api/client.ts";
import type { ClientBookingsResponse } from "../api/types.ts";

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  phone: string;
  token: string | null;
  setPhone: (phone: string) => void;
  setAuthenticated: (auth: boolean, token?: string) => void;
  checkSession: () => Promise<void>;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  isAuthenticated: false,
  isLoading: true,
  phone: "",
  token: localStorage.getItem("client_token"),

  setPhone: (phone) => set({ phone }),

  setAuthenticated: (auth, token?) => {
    if (token) {
      localStorage.setItem("client_token", token);
    }
    set({ isAuthenticated: auth, isLoading: false, token: token ?? null });
  },

  checkSession: async () => {
    set({ isLoading: true });
    try {
      const headers: Record<string, string> = {};
      const savedToken = localStorage.getItem("client_token");
      if (savedToken) {
        headers["Authorization"] = `Bearer ${savedToken}`;
      }
      await apiRequest<ClientBookingsResponse>("/client/bookings", {
        credentials: "include",
        headers,
      });
      set({ isAuthenticated: true, isLoading: false, token: savedToken });
    } catch {
      localStorage.removeItem("client_token");
      set({ isAuthenticated: false, isLoading: false, token: null });
    }
  },

  logout: () => {
    localStorage.removeItem("client_token");
    set({ isAuthenticated: false, phone: "", token: null });
  },
}));

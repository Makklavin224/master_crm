import { create } from "zustand";
import { apiRequest } from "../api/client.ts";
import type { ClientBookingsResponse } from "../api/types.ts";

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  phone: string;
  setPhone: (phone: string) => void;
  setAuthenticated: (auth: boolean) => void;
  checkSession: () => Promise<void>;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  isAuthenticated: false,
  isLoading: true,
  phone: "",

  setPhone: (phone) => set({ phone }),

  setAuthenticated: (auth) => set({ isAuthenticated: auth, isLoading: false }),

  checkSession: async () => {
    set({ isLoading: true });
    try {
      await apiRequest<ClientBookingsResponse>("/client/bookings", {
        credentials: "include",
      });
      set({ isAuthenticated: true, isLoading: false });
    } catch {
      set({ isAuthenticated: false, isLoading: false });
    }
  },

  logout: () => set({ isAuthenticated: false, phone: "" }),
}));

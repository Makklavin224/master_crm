import { create } from "zustand";

interface AuthState {
  role: "client" | "master" | null;
  masterId: string | null;
  tgUserId: string | null;
  initDataRaw: string | null;
  setRole: (role: "client" | "master" | null) => void;
  setMasterId: (id: string | null) => void;
  setTgUserId: (id: string | null) => void;
  setInitDataRaw: (data: string | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  role: null,
  masterId: null,
  tgUserId: null,
  initDataRaw: null,
  setRole: (role) => set({ role }),
  setMasterId: (masterId) => set({ masterId }),
  setTgUserId: (tgUserId) => set({ tgUserId }),
  setInitDataRaw: (initDataRaw) => set({ initDataRaw }),
}));

import { create } from "zustand";

function getStoredTheme(): boolean {
  try {
    return typeof localStorage !== "undefined" &&
      localStorage.getItem("admin_theme") === "dark";
  } catch {
    return false;
  }
}

function saveTheme(isDark: boolean): void {
  try {
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("admin_theme", isDark ? "dark" : "light");
    }
  } catch {
    // Ignore storage errors (SSR, restricted environments)
  }
}

interface ThemeState {
  isDark: boolean;
  toggle: () => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  isDark: getStoredTheme(),
  toggle: () =>
    set((s) => {
      const next = !s.isDark;
      saveTheme(next);
      return { isDark: next };
    }),
}));

import type { Platform } from "./types.ts";

declare global {
  interface Window {
    Telegram?: {
      WebApp?: Record<string, unknown>;
    };
  }
}

export function detectPlatform(): Platform {
  if (typeof window !== "undefined" && window.Telegram?.WebApp) {
    return "telegram";
  }
  return "web";
}

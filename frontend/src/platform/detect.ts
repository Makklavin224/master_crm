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

  // Check MAX -- WebApp object injected by max-web-app.js (no window.Telegram)
  if (
    typeof window !== "undefined" &&
    (window as any).WebApp?.initData !== undefined
  ) {
    return "max";
  }

  // Check VK -- launch params in URL
  if (typeof window !== "undefined") {
    const params = new URLSearchParams(window.location.search);
    if (params.has("vk_user_id") && params.has("sign")) {
      return "vk";
    }
  }

  return "web";
}

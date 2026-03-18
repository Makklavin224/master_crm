import bridge from "@vkontakte/vk-bridge";
import type { PlatformBridge } from "../types.ts";

export function createVkBridge(): PlatformBridge {
  // Initialize VK Bridge
  bridge.send("VKWebAppInit");

  // Cache launch params from URL
  const urlParams = new URLSearchParams(window.location.search);
  const vkUserId = urlParams.get("vk_user_id");

  return {
    platform: "vk",

    getInitDataRaw(): string | null {
      // VK uses URL query string as launch params
      return window.location.search.slice(1) || null;
    },

    getUserId(): string | null {
      return vkUserId;
    },

    hapticFeedback(type: "light" | "medium" | "heavy"): void {
      try {
        bridge.send("VKWebAppTapticImpactOccurred", { style: type });
      } catch {
        // Haptic feedback may not be supported
      }
    },

    showBackButton(): void {
      /* VK has no native back button API */
    },

    hideBackButton(): void {
      /* No-op for VK */
    },

    onBackButtonClick(): () => void {
      return () => {};
      /* VK has no back button events */
    },

    ready(): void {
      /* VKWebAppInit already called */
    },

    expand(): void {
      /* VK Mini Apps auto-expand */
    },

    close(): void {
      try {
        bridge.send("VKWebAppClose", { status: "success" });
      } catch {
        // May fail outside VK environment
      }
    },
  };
}

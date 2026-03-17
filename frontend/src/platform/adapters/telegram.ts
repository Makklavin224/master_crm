import {
  init,
  miniAppReady,
  expandViewport,
  closeMiniApp,
  showBackButton,
  hideBackButton,
  onBackButtonClick,
  offBackButtonClick,
  mountBackButton,
  hapticFeedbackImpactOccurred,
  retrieveRawInitData,
  retrieveLaunchParams,
} from "@telegram-apps/sdk-react";
import type { PlatformBridge } from "../types.ts";

export function createTelegramBridge(): PlatformBridge {
  // Initialize the SDK -- must be called before using any SDK functions
  const cleanup = init();

  // Mount back button component so show/hide work
  try {
    mountBackButton();
  } catch {
    // Back button mount may fail in some environments
  }

  // Cache user ID from launch params
  let cachedUserId: string | null = null;
  try {
    const lp = retrieveLaunchParams(true);
    const initData = lp.tgWebAppData;
    if (initData && typeof initData === "object" && "user" in initData) {
      const user = (initData as Record<string, unknown>).user;
      if (user && typeof user === "object" && "id" in user) {
        cachedUserId = String((user as Record<string, unknown>).id);
      }
    }
  } catch {
    // Launch params may not be available in all contexts
  }

  // Cache raw init data
  let cachedInitDataRaw: string | null = null;
  try {
    cachedInitDataRaw = retrieveRawInitData() ?? null;
  } catch {
    // May not be available
  }

  return {
    platform: "telegram",

    getInitDataRaw(): string | null {
      return cachedInitDataRaw;
    },

    getUserId(): string | null {
      return cachedUserId;
    },

    hapticFeedback(type: "light" | "medium" | "heavy"): void {
      try {
        hapticFeedbackImpactOccurred(type);
      } catch {
        // Haptic feedback may not be supported
      }
    },

    showBackButton(): void {
      try {
        showBackButton();
      } catch {
        // May not be supported
      }
    },

    hideBackButton(): void {
      try {
        hideBackButton();
      } catch {
        // May not be supported
      }
    },

    onBackButtonClick(cb: () => void): () => void {
      try {
        onBackButtonClick(cb);
        return () => {
          try {
            offBackButtonClick(cb);
          } catch {
            // Cleanup may fail
          }
        };
      } catch {
        return () => {};
      }
    },

    ready(): void {
      try {
        miniAppReady();
      } catch {
        // May fail outside TG environment
      }
    },

    expand(): void {
      try {
        expandViewport();
      } catch {
        // May not be supported
      }
    },

    close(): void {
      try {
        closeMiniApp();
      } catch {
        // May fail outside TG
      }
    },

    // Cleanup function -- call to remove SDK listeners
    _cleanup: cleanup,
  } as PlatformBridge & { _cleanup: VoidFunction };
}

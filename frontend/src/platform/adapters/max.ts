import type { PlatformBridge } from "../types.ts";

/**
 * MAX Bridge adapter.
 *
 * Wraps `window.WebApp` injected by max-web-app.js.
 * MAX Bridge has NO: expand(), MainButton, showAlert(), showConfirm(), CloudStorage.
 */
export function createMaxBridge(): PlatformBridge {
  const webApp = (window as any).WebApp;

  return {
    platform: "max",

    getInitDataRaw(): string | null {
      return webApp?.initData ?? null;
    },

    getUserId(): string | null {
      return webApp?.initDataUnsafe?.user?.id?.toString() ?? null;
    },

    hapticFeedback(type: "light" | "medium" | "heavy"): void {
      try {
        webApp?.HapticFeedback?.impactOccurred(type);
      } catch {
        // Haptic feedback may not be supported in MAX
      }
    },

    showBackButton(): void {
      try {
        webApp?.BackButton?.show();
      } catch {
        // May not be supported
      }
    },

    hideBackButton(): void {
      try {
        webApp?.BackButton?.hide();
      } catch {
        // May not be supported
      }
    },

    onBackButtonClick(cb: () => void): () => void {
      try {
        webApp?.BackButton?.onClick(cb);
        return () => {
          try {
            webApp?.BackButton?.offClick(cb);
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
        webApp?.ready();
      } catch {
        // May fail outside MAX environment
      }
    },

    expand(): void {
      // MAX has NO expand() -- no-op (Pitfall 7 from RESEARCH.md)
    },

    close(): void {
      try {
        webApp?.close();
      } catch {
        // May fail outside MAX environment
      }
    },
  };
}

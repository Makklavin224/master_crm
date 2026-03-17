import type { PlatformBridge } from "../types.ts";

export function createStubBridge(): PlatformBridge {
  return {
    platform: "web",

    getInitDataRaw(): string | null {
      return null;
    },

    getUserId(): string | null {
      return "dev-user-123";
    },

    hapticFeedback(): void {
      // No-op in web/dev mode
    },

    showBackButton(): void {
      // No-op in web/dev mode
    },

    hideBackButton(): void {
      // No-op in web/dev mode
    },

    onBackButtonClick(): () => void {
      return () => {};
    },

    ready(): void {
      // No-op in web/dev mode
    },

    expand(): void {
      // No-op in web/dev mode
    },

    close(): void {
      // No-op in web/dev mode -- could redirect or show message
      console.info("[StubBridge] close() called -- no-op in web mode");
    },
  };
}

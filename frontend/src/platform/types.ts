export type Platform = "telegram" | "max" | "vk" | "web";

export interface PlatformBridge {
  platform: Platform;
  getInitDataRaw(): string | null;
  getUserId(): string | null;
  hapticFeedback(type: "light" | "medium" | "heavy"): void;
  showBackButton(): void;
  hideBackButton(): void;
  onBackButtonClick(cb: () => void): () => void;
  ready(): void;
  expand(): void;
  close(): void;
}

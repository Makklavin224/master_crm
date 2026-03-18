import { createContext, useContext, useEffect, useMemo, type ReactNode } from "react";
import type { PlatformBridge } from "./types.ts";
import { detectPlatform } from "./detect.ts";
import { createTelegramBridge } from "./adapters/telegram.ts";
import { createMaxBridge } from "./adapters/max.ts";
import { createVkBridge } from "./adapters/vk.ts";
import { createStubBridge } from "./adapters/stub.ts";

const PlatformContext = createContext<PlatformBridge | null>(null);

interface PlatformProviderProps {
  children: ReactNode;
}

export function PlatformProvider({ children }: PlatformProviderProps) {
  const bridge = useMemo(() => {
    const platform = detectPlatform();
    switch (platform) {
      case "telegram":
        return createTelegramBridge();
      case "max":
        return createMaxBridge();
      case "vk":
        return createVkBridge();
      default:
        return createStubBridge();
    }
  }, []);

  useEffect(() => {
    bridge.ready();
    bridge.expand();
  }, [bridge]);

  return (
    <PlatformContext.Provider value={bridge}>
      {children}
    </PlatformContext.Provider>
  );
}

export function usePlatform(): PlatformBridge {
  const bridge = useContext(PlatformContext);
  if (!bridge) {
    throw new Error("usePlatform must be used within a PlatformProvider");
  }
  return bridge;
}

import { describe, it, expect, beforeEach } from "vitest";
import { useThemeStore } from "../../stores/theme";

beforeEach(() => {
  useThemeStore.setState({ isDark: false });
});

describe("useThemeStore", () => {
  it("initializes with isDark=false", () => {
    const state = useThemeStore.getState();
    expect(state.isDark).toBe(false);
  });

  it("toggle flips isDark", () => {
    useThemeStore.getState().toggle();
    expect(useThemeStore.getState().isDark).toBe(true);

    useThemeStore.getState().toggle();
    expect(useThemeStore.getState().isDark).toBe(false);
  });
});

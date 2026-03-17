import { describe, it, expect } from "vitest";
import { formatPrice, formatDuration, formatDate, formatTime } from "../format.ts";

describe("formatPrice", () => {
  it("formats kopecks to rubles with space separator", () => {
    expect(formatPrice(250000)).toBe("2\u00A0500 \u20BD");
  });
  it("formats zero", () => {
    expect(formatPrice(0)).toBe("0 \u20BD");
  });
  it("formats small amounts", () => {
    expect(formatPrice(100)).toBe("1 \u20BD");
  });
  it("formats large amounts", () => {
    expect(formatPrice(1000000)).toBe("10\u00A0000 \u20BD");
  });
});

describe("formatDuration", () => {
  it("formats hours only", () => {
    expect(formatDuration(60)).toBe("1 ч");
  });
  it("formats hours and minutes", () => {
    expect(formatDuration(90)).toBe("1 ч 30 мин");
  });
  it("formats minutes only", () => {
    expect(formatDuration(30)).toBe("30 мин");
  });
  it("formats two hours", () => {
    expect(formatDuration(120)).toBe("2 ч");
  });
});

describe("formatDate", () => {
  it("formats ISO date string", () => {
    expect(formatDate("2026-03-25")).toBe("25 марта 2026");
  });
  it("formats Date object", () => {
    expect(formatDate(new Date(2026, 0, 15))).toBe("15 января 2026");
  });
});

describe("formatTime", () => {
  it("passes time through", () => {
    expect(formatTime("14:00")).toBe("14:00");
  });
});

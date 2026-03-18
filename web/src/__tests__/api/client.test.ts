import { describe, it, expect, beforeEach, vi } from "vitest";
import { apiRequest, ApiError } from "../../api/client";
import { useAuth } from "../../stores/auth";

beforeEach(() => {
  useAuth.setState({
    token: "test-bearer-token",
    isAuthenticated: true,
    isLoading: false,
    error: null,
  });
  vi.unstubAllGlobals();
});

describe("apiRequest", () => {
  it("attaches Authorization header from auth store", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: "test" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await apiRequest("/test");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/test"),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-bearer-token",
        }),
      }),
    );
  });

  it("throws ApiError on non-ok response", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: "Bad request" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await expect(apiRequest("/test")).rejects.toThrow(ApiError);
    await expect(apiRequest("/test")).rejects.toMatchObject({
      status: 400,
      detail: "Bad request",
    });
  });
});

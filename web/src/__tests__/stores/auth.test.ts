import { describe, it, expect, beforeEach, vi } from "vitest";
import { useAuth } from "../../stores/auth";

// Reset store between tests
beforeEach(() => {
  useAuth.setState({
    token: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  });
});

describe("useAuth", () => {
  it("initializes with isAuthenticated=false and token=null", () => {
    const state = useAuth.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.token).toBeNull();
  });

  it("loginEmail calls fetch with correct endpoint", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ access_token: "test-jwt-token" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await useAuth.getState().loginEmail("test@example.com", "password123");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/auth/login"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "test@example.com", password: "password123" }),
      }),
    );

    const state = useAuth.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.token).toBe("test-jwt-token");

    vi.unstubAllGlobals();
  });

  it("logout clears token", () => {
    // Simulate logged-in state
    useAuth.setState({ token: "some-token", isAuthenticated: true });

    useAuth.getState().logout();

    const state = useAuth.getState();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });
});

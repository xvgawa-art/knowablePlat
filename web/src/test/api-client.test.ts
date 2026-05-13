import { describe, it, expect, vi, beforeEach } from "vitest";

describe("api client", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("attaches auth token from localStorage to requests", async () => {
    localStorage.setItem("token", "test-jwt-token");

    const mockFetch = vi.fn().mockResolvedValue({
      status: 200,
      ok: true,
      json: () => Promise.resolve({ id: "1", name: "test" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { api } = await import("../api/client");
    await api.get("/test");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/test",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-jwt-token",
        }),
      }),
    );
  });

  it("omits auth header when no token stored", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      status: 200,
      ok: true,
      json: () => Promise.resolve([]),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { api } = await import("../api/client");
    await api.get("/items");

    const callArgs = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(callArgs[1].headers).not.toHaveProperty("Authorization");
  });

  it("throws on non-ok response with detail message", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      status: 404,
      ok: false,
      json: () => Promise.resolve({ detail: "资源不存在" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { api } = await import("../api/client");

    await expect(api.get("/missing")).rejects.toThrow("资源不存在");
  });

  it("throws generic error when no detail", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      status: 500,
      ok: false,
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { api } = await import("../api/client");

    await expect(api.get("/error")).rejects.toThrow("请求失败: 500");
  });

  it("returns undefined for 204 no content", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      status: 204,
      ok: true,
    });
    vi.stubGlobal("fetch", mockFetch);

    const { api } = await import("../api/client");
    const result = await api.del("/item/1");

    expect(result).toBeUndefined();
  });

  it("sends POST with JSON body", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      status: 201,
      ok: true,
      json: () => Promise.resolve({ id: "new" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { api } = await import("../api/client");
    await api.post("/items", { name: "test" });

    const callArgs = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(callArgs[1].method).toBe("POST");
    expect(callArgs[1].body).toBe(JSON.stringify({ name: "test" }));
  });

  it("appends query params for get with params", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      status: 200,
      ok: true,
      json: () => Promise.resolve([]),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { api } = await import("../api/client");
    await api.get("/items", { page: 1, limit: 10 });

    const url = (mockFetch.mock.calls[0] as [string])[0];
    expect(url).toContain("page=1");
    expect(url).toContain("limit=10");
  });
});

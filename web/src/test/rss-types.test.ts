import { describe, it, expect } from "vitest";
import { parseList, buildList, EMPTY_FORM, STATUS_MAP, ENTRY_STATUS } from "../components/rss/types";

describe("parseList", () => {
  it("joins array values with comma-space", () => {
    expect(parseList(["a", "b", "c"])).toBe("a, b, c");
  });

  it("returns empty string for null", () => {
    expect(parseList(null)).toBe("");
  });

  it("returns empty string for undefined", () => {
    expect(parseList(undefined)).toBe("");
  });

  it("handles single item", () => {
    expect(parseList(["only"])).toBe("only");
  });

  it("handles empty array", () => {
    expect(parseList([])).toBe("");
  });
});

describe("buildList", () => {
  it("splits comma-separated values and trims", () => {
    expect(buildList("a, b, c")).toEqual(["a", "b", "c"]);
  });

  it("returns null for empty string", () => {
    expect(buildList("")).toBeNull();
  });

  it("returns null for whitespace-only string", () => {
    expect(buildList("   ,  ,  ")).toBeNull();
  });

  it("handles single value", () => {
    expect(buildList("XSS")).toEqual(["XSS"]);
  });

  it("trims whitespace around values", () => {
    expect(buildList("  foo  ,  bar  ")).toEqual(["foo", "bar"]);
  });
});

describe("EMPTY_FORM", () => {
  it("has correct default values", () => {
    expect(EMPTY_FORM.name).toBe("");
    expect(EMPTY_FORM.url).toBe("");
    expect(EMPTY_FORM.filter_keywords).toBe("");
    expect(EMPTY_FORM.filter_authors).toBe("");
    expect(EMPTY_FORM.filter_categories).toBe("");
    expect(EMPTY_FORM.poll_interval).toBe(60);
  });
});

describe("STATUS_MAP", () => {
  it("has success, partial, and failed entries", () => {
    expect(STATUS_MAP.success).toBeDefined();
    expect(STATUS_MAP.partial).toBeDefined();
    expect(STATUS_MAP.failed).toBeDefined();
  });

  it("each entry has label and color", () => {
    for (const entry of Object.values(STATUS_MAP)) {
      expect(entry).toHaveProperty("label");
      expect(entry).toHaveProperty("color");
    }
  });
});

describe("ENTRY_STATUS", () => {
  it("has all expected statuses", () => {
    expect(ENTRY_STATUS.new).toBeDefined();
    expect(ENTRY_STATUS.ingesting).toBeDefined();
    expect(ENTRY_STATUS.completed).toBeDefined();
    expect(ENTRY_STATUS.filtered).toBeDefined();
    expect(ENTRY_STATUS.failed).toBeDefined();
  });
});

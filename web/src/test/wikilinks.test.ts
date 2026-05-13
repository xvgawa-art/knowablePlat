import { describe, it, expect } from "vitest";

// Re-implement the transformWikilinks logic for unit testing.
// The actual function is not exported, so we replicate it here.
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^\w一-鿿-]/g, "");
}

function transformWikilinks(content: string, kbSlug?: string): string {
  return content.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_match, target, label) => {
    const displayText = label || target;
    if (kbSlug) {
      const slug = slugify(target);
      return `[${displayText}](/kb/${kbSlug}/wiki/${encodeURIComponent(slug)})`;
    }
    return `**${displayText}**`;
  });
}

describe("transformWikilinks", () => {
  it("converts basic wikilinks to markdown links", () => {
    const result = transformWikilinks("See [[xss-attack]] for details.", "web-security");
    expect(result).toBe("See [xss-attack](/kb/web-security/wiki/xss-attack) for details.");
  });

  it("handles wikilinks with display labels", () => {
    const result = transformWikilinks("Learn about [[sql-injection|SQL 注入]] here.", "web-security");
    expect(result).toBe("Learn about [SQL 注入](/kb/web-security/wiki/sql-injection) here.");
  });

  it("bolds wikilinks when no kbSlug provided", () => {
    const result = transformWikilinks("See [[some-concept]] for info.");
    expect(result).toBe("See **some-concept** for info.");
  });

  it("handles multiple wikilinks in one string", () => {
    const result = transformWikilinks("[[a]] and [[b|B]] and [[c]]", "kb1");
    expect(result).toContain("[a](/kb/kb1/wiki/a)");
    expect(result).toContain("[B](/kb/kb1/wiki/b)");
    expect(result).toContain("[c](/kb/kb1/wiki/c)");
  });

  it("slugifies wikilinks with spaces", () => {
    const result = transformWikilinks("[[XSS Attack]]", "kb1");
    expect(result).toBe("[XSS Attack](/kb/kb1/wiki/xss-attack)");
  });

  it("handles Chinese characters in wikilinks", () => {
    const result = transformWikilinks("[[网络安全]]", "kb1");
    expect(result).toContain("/kb/kb1/wiki/");
    expect(result).toContain(encodeURIComponent("网络安全"));
  });

  it("leaves non-wikilink text unchanged", () => {
    const input = "Normal text with [regular link](https://example.com)";
    const result = transformWikilinks(input, "kb1");
    expect(result).toBe(input);
  });
});

describe("slugify", () => {
  it("lowercases text", () => {
    expect(slugify("Hello World")).toBe("hello-world");
  });

  it("replaces spaces with hyphens", () => {
    expect(slugify("cross site scripting")).toBe("cross-site-scripting");
  });

  it("preserves Chinese characters", () => {
    expect(slugify("网络扫描工具")).toBe("网络扫描工具");
  });

  it("removes special characters", () => {
    expect(slugify("tool@name!#123")).toBe("toolname123");
  });
});

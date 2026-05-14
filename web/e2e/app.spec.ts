import { test, expect } from "@playwright/test";

test.describe("仪表盘", () => {
  test("加载首页，显示仪表盘标题", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("仪表盘");
  });

  test("侧边栏导航项可见", async ({ page }) => {
    await page.goto("/");
    const sidebar = page.locator("aside");
    await expect(sidebar).toBeVisible();
    await expect(sidebar.locator("text=知识库管理")).toBeVisible();
    await expect(sidebar.locator("text=工具装备库")).toBeVisible();
    await expect(sidebar.locator("text=知识生成")).toBeVisible();
    await expect(sidebar.locator("text=通知")).toBeVisible();
  });
});

test.describe("知识库管理", () => {
  test("显示知识库列表页", async ({ page }) => {
    await page.goto("/kb");
    await expect(page.locator("h1")).toContainText("知识库管理");
    await expect(page.locator("text=创建知识库")).toBeVisible();
  });

  test("创建知识库表单可见", async ({ page }) => {
    await page.goto("/kb");
    await expect(page.locator('input[placeholder*="Web 安全"]')).toBeVisible();
    await expect(page.locator('input[placeholder*="web-security"]')).toBeVisible();
    await expect(page.locator('button:has-text("创建")')).toBeVisible();
  });

  test("分页组件可见（当有多条数据时）", async ({ page }) => {
    await page.goto("/kb");
    const pagination = page.locator("text=显示");
    if (await pagination.isVisible()) {
      await expect(page.locator("text=上一页")).toBeVisible();
      await expect(page.locator("text=下一页")).toBeVisible();
    }
  });
});

test.describe("来源列表分页和批量删除", () => {
  test("来源列表页显示分页控件", async ({ page }) => {
    const response = await page.goto("/");
    await page.goto("/kb");
    const kbLink = page.locator("a[href*='/kb/']").first();
    if (await kbLink.isVisible()) {
      await kbLink.click();
      await page.waitForURL(/\/kb\/[^/]+$/);
      await page.locator('a:has-text("来源")').click();
      await page.waitForURL(/\/sources$/);
      const pagination = page.locator("text=显示");
      if (await pagination.isVisible()) {
        await expect(page.locator("text=上一页")).toBeVisible();
      }
    }
  });
});

test.describe("通知中心", () => {
  test("通知列表页加载", async ({ page }) => {
    await page.goto("/notifications");
    await expect(page.locator("h1")).toContainText("通知中心");
  });

  test("通知筛选控件可见", async ({ page }) => {
    await page.goto("/notifications");
    await expect(page.locator("main select")).toBeVisible();
    await expect(page.locator('button:has-text("仅未读")')).toBeVisible();
    await expect(page.locator('button:has-text("全部已读")')).toBeVisible();
  });
});

test.describe("Wiki 浏览", () => {
  test("Wiki 列表页类型筛选可见", async ({ page }) => {
    await page.goto("/kb");
    const kbLink = page.locator("a[href*='/kb/']").first();
    if (await kbLink.isVisible()) {
      await kbLink.click();
      await page.waitForURL(/\/kb\/[^/]+$/);
      await page.locator('a:has-text("Wiki")').click();
      await page.waitForURL(/\/wiki$/);
      await expect(page.locator("h1")).toContainText("Wiki");
    }
  });
});

test.describe("生成历史", () => {
  test("生成历史页面加载", async ({ page }) => {
    await page.goto("/generate/history");
    await expect(page.locator("h1")).toContainText("生成历史");
  });
});

test.describe("工具装备库", () => {
  test("工具装备库页面加载", async ({ page }) => {
    await page.goto("/tools");
    await expect(page.locator("h1")).toContainText("工具装备库");
  });
});

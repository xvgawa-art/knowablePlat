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

  test("创建知识库表单提交", async ({ page }) => {
    const apiPromise = page.waitForResponse(
      (resp) => resp.url().includes("/api/knowledge-bases") && resp.request().method() === "POST"
    );
    await page.goto("/kb");
    const rand = Math.random().toString(36).slice(2, 10);
    await page.locator('input[placeholder*="Web 安全"]').fill(`E2E测试-${rand}`);
    await page.locator('input[placeholder*="web-security"]').fill(`e2e-${rand}`);
    await page.getByRole("button", { name: "创建" }).click();
    const response = await apiPromise;
    expect([200, 201]).toContain(response.status());
  });

  test("分页组件可见（当有多条数据时）", async ({ page }) => {
    await page.goto("/kb");
    const pagination = page.locator("text=显示");
    if (await pagination.isVisible()) {
      await expect(page.locator("text=上一页")).toBeVisible();
      await expect(page.locator("text=下一页")).toBeVisible();
    }
  });

  test("知识库列表有全选复选框", async ({ page }) => {
    await page.goto("/kb");
    await page.waitForTimeout(500);
    const checkboxes = page.locator('input[type="checkbox"]');
    const count = await checkboxes.count();
    if (count > 0) {
      await expect(checkboxes.first()).toBeVisible();
    }
  });
});

test.describe("知识库详情页", () => {
  test("进入知识库详情页", async ({ page }) => {
    await page.goto("/kb");
    await page.waitForTimeout(500);
    const enterBtn = page.locator('a:has-text("进入")').first();
    if (await enterBtn.isVisible()) {
      await enterBtn.click();
      await page.waitForURL(/\/kb\/[^/]+$/);
      await expect(page.locator("h1")).toBeVisible();
      await expect(page.locator("text=来源文档")).toBeVisible();
      await expect(page.locator("text=Wiki 页面")).toBeVisible();
      await expect(page.locator('a:has-text("提交 URL")')).toBeVisible();
    }
  });

  test("知识库详情页导航链接", async ({ page }) => {
    await page.goto("/kb");
    await page.waitForTimeout(500);
    const enterBtn = page.locator('a:has-text("进入")').first();
    if (await enterBtn.isVisible()) {
      await enterBtn.click();
      await page.waitForURL(/\/kb\/[^/]+$/);
      await expect(page.locator('a:has-text("查看全部")')).toHaveCount(2);
      await expect(page.locator('a:has-text("浏览 Wiki")')).toBeVisible();
      await expect(page.locator('a:has-text("对话查询")')).toBeVisible();
    }
  });
});

test.describe("来源列表", () => {
  test("来源列表页显示分页控件", async ({ page }) => {
    await page.goto("/");
    await page.goto("/kb");
    const kbLink = page.locator("a[href*='/kb/']").first();
    if (await kbLink.isVisible()) {
      await kbLink.click();
      await page.waitForURL(/\/kb\/[^/]+$/);
      await page.locator('a:has-text("来源")').click();
      await page.waitForURL(/\/sources$/);
      await expect(page.locator("h1")).toContainText("来源列表");
      await expect(page.locator('a:has-text("提交 URL")')).toBeVisible();
    }
  });

  test("来源列表有提交URL链接", async ({ page }) => {
    await page.goto("/kb");
    await page.waitForTimeout(500);
    const enterBtn = page.locator('a:has-text("进入")').first();
    if (await enterBtn.isVisible()) {
      await enterBtn.click();
      await page.waitForURL(/\/kb\/[^/]+$/);
      const sourceLink = page.locator('a:has-text("来源")');
      if (await sourceLink.isVisible()) {
        await sourceLink.click();
        await page.waitForURL(/\/sources/);
        await expect(page.locator('a:has-text("提交 URL")')).toBeVisible();
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

  test("通知知识库筛选下拉可交互", async ({ page }) => {
    await page.goto("/notifications");
    await page.waitForTimeout(500);
    const select = page.locator("main select");
    await select.selectOption({ index: 0 });
    await expect(select).toBeVisible();
  });

  test("仅未读按钮切换", async ({ page }) => {
    await page.goto("/notifications");
    const btn = page.locator('button:has-text("仅未读")');
    await btn.click();
    await expect(page.locator('button:has-text("显示全部")')).toBeVisible();
    await page.locator('button:has-text("显示全部")').click();
    await expect(page.locator('button:has-text("仅未读")')).toBeVisible();
  });

  test("通知列表有全选复选框", async ({ page }) => {
    await page.goto("/notifications");
    await page.waitForTimeout(500);
    const checkboxes = page.locator('input[type="checkbox"]');
    const count = await checkboxes.count();
    if (count > 0) {
      await expect(checkboxes.first()).toBeVisible();
    }
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

  test("Wiki 页面搜索栏可见", async ({ page }) => {
    await page.goto("/kb");
    const kbLink = page.locator("a[href*='/kb/']").first();
    if (await kbLink.isVisible()) {
      await kbLink.click();
      await page.waitForURL(/\/kb\/[^/]+$/);
      await page.locator('a:has-text("Wiki")').click();
      await page.waitForURL(/\/wiki$/);
      await expect(page.locator('input[placeholder*="关键词"]')).toBeVisible();
      await expect(page.locator('button:has-text("搜索")')).toBeVisible();
      await expect(page.locator('text=关键词')).toBeVisible();
    }
  });

  test("Wiki 页面类型筛选按钮可见", async ({ page }) => {
    await page.goto("/kb");
    const kbLink = page.locator("a[href*='/kb/']").first();
    if (await kbLink.isVisible()) {
      await kbLink.click();
      await page.waitForURL(/\/kb\/[^/]+$/);
      await page.locator('a:has-text("Wiki")').click();
      await page.waitForURL(/\/wiki$/);
      await expect(page.locator('button:has-text("全部")')).toBeVisible();
      await expect(page.locator('button:has-text("来源")')).toBeVisible();
      await expect(page.locator('button:has-text("实体")')).toBeVisible();
      await expect(page.locator('button:has-text("概念")')).toBeVisible();
    }
  });

  test("Wiki 类型筛选可点击切换", async ({ page }) => {
    await page.goto("/kb");
    const kbLink = page.locator("a[href*='/kb/']").first();
    if (await kbLink.isVisible()) {
      await kbLink.click();
      await page.waitForURL(/\/kb\/[^/]+$/);
      await page.locator('a:has-text("Wiki")').click();
      await page.waitForURL(/\/wiki$/);
      await page.locator('button:has-text("来源")').click();
      await page.waitForTimeout(300);
      await expect(page.locator('button:has-text("来源")')).toBeVisible();
    }
  });
});

test.describe("生成历史", () => {
  test("生成历史页面加载", async ({ page }) => {
    await page.goto("/generate/history");
    await expect(page.locator("h1")).toContainText("生成历史");
  });

  test("生成历史有新建生成链接", async ({ page }) => {
    await page.goto("/generate/history");
    await expect(page.locator('a:has-text("新建生成")')).toBeVisible();
  });

  test("生成历史全选复选框", async ({ page }) => {
    await page.goto("/generate/history");
    await page.waitForTimeout(500);
    const checkboxes = page.locator('input[type="checkbox"]');
    const count = await checkboxes.count();
    if (count > 0) {
      await expect(checkboxes.first()).toBeVisible();
    }
  });
});

test.describe("工具装备库", () => {
  test("工具装备库页面加载", async ({ page }) => {
    await page.goto("/tools");
    await expect(page.locator("h1")).toContainText("工具装备库");
  });
});

test.describe("知识生成", () => {
  test("知识生成页面加载", async ({ page }) => {
    await page.goto("/generate");
    await expect(page.locator("h1")).toBeVisible();
  });
});

test.describe("分页交互", () => {
  test("知识库列表分页导航", async ({ page }) => {
    await page.goto("/kb");
    await page.waitForTimeout(500);
    const nextBtn = page.locator('button:has-text("下一页")');
    if (await nextBtn.isVisible() && await nextBtn.isEnabled()) {
      await nextBtn.click();
      await page.waitForTimeout(500);
      await expect(page.locator("text=上一页")).toBeVisible();
    }
  });

  test("生成历史分页导航", async ({ page }) => {
    await page.goto("/generate/history");
    await page.waitForTimeout(500);
    const nextBtn = page.locator('button:has-text("下一页")');
    if (await nextBtn.isVisible() && await nextBtn.isEnabled()) {
      await nextBtn.click();
      await page.waitForTimeout(500);
      await expect(page.locator("text=上一页")).toBeVisible();
    }
  });
});

test.describe("404 页面", () => {
  test("访问不存在的路由显示404", async ({ page }) => {
    await page.goto("/nonexistent-page");
    await expect(page.locator("text=404")).toBeVisible();
    await expect(page.locator('a:has-text("返回首页")')).toBeVisible();
  });
});

test.describe("RSS 管理", () => {
  test("RSS 管理页面加载", async ({ page }) => {
    await page.goto("/kb");
    const enterBtn = page.locator('a:has-text("进入")').first();
    if (await enterBtn.isVisible()) {
      await enterBtn.click();
      await page.waitForURL(/\/kb\/[^/]+$/);
      await page.locator('a:has-text("RSS")').click();
      await page.waitForURL(/\/rss$/);
      await expect(page.locator("h1")).toContainText("RSS");
      await expect(page.locator('button:has-text("添加订阅")')).toBeVisible();
    }
  });
});

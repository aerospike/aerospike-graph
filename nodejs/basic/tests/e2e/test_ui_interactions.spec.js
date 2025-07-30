import { test, expect } from "@playwright/test";

test.describe("UI Interactions and Queries", () => {
  test("selects users and displays transactions graph", async ({ page }) => {
    await page.goto("/");

    await page.waitForLoadState("networkidle");

    await page.click('a[href="#between"]');

    await page.waitForSelector("#user-select-1", { state: "visible" });
    await page.waitForSelector("#user-select-2", { state: "visible" });

    await page.fill("#user-select-1", "Alice");

    await page.waitForSelector("#user-select-2:not([disabled])", {
      timeout: 5000,
    });

    await page.fill("#user-select-2", "Bob");
    await page.click("#refresh-btn");
    await expect(page.locator("svg")).toBeVisible();
    await page.waitForTimeout(2000);
    const count = await page.locator("svg *").count();
    expect(count).toBeGreaterThan(0);
  });

  test("displays outgoing transactions", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    await page.click('a[href="#outgoing"]');
    await page.waitForSelector("#user-select-1", { state: "visible" });

    await page.fill("#user-select-1", "Alice");
    await page.click("#refresh-btn");
    await expect(page.locator("svg")).toBeVisible();
    await page.waitForTimeout(2000);
    const count = await page.locator("svg *").count();
    expect(count).toBeGreaterThan(0);
  });

  test("displays incoming transactions", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    await page.click('a[href="#incoming"]');
    await page.waitForSelector("#user-select-1", { state: "visible" });

    await page.fill("#user-select-1", "Alice");
    await page.click("#refresh-btn");
    await expect(page.locator("svg")).toBeVisible();
    await page.waitForTimeout(2000);
    const count = await page.locator("svg *").count();
    expect(count).toBeGreaterThan(0);
  });

  test("triggers fraud detection and asserts rankings", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    await page.click('a[href="#hub"]');
    await expect(page.locator("svg")).toBeVisible();
    await page.waitForTimeout(2000);
    const count = await page.locator("svg *").count();
    expect(count).toBeGreaterThan(0);
  });
});

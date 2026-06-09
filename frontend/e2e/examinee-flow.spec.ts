import { test, expect } from "@playwright/test";

const API_BASE =
  process.env.PLAYWRIGHT_API_BASE_URL ?? "http://localhost:8000/api/v1";

test.describe("Examinee flow", () => {
  test.skip(!process.env.E2E_WITH_API, "Set E2E_WITH_API=1 with backend running");

  test("entry form validates PRN format", async ({ page }) => {
    await page.goto("/");
    await page.getByText("Enter as Examinee").click();
    await page.getByLabel(/Permanent Registration Number/i).fill("invalid prn!");
    await page.getByLabel(/Full Name/i).fill("Test User");
    await page.getByLabel(/privacy notice/i).check();
    await page.getByRole("button", { name: /Start Test/i }).click();
    await expect(page.getByRole("alert")).toBeVisible();
  });

  test("full examinee flow with API", async ({ page, request }) => {
    const health = await request.get(`${API_BASE}/health`);
    test.skip(!health.ok(), "Backend not available");

    const prn = `E2E${Date.now().toString().slice(-8)}`;
    await page.goto("/");
    await page.getByText("Enter as Examinee").click();
    await page.getByLabel(/Permanent Registration Number/i).fill(prn);
    await page.getByLabel(/Full Name/i).fill("E2E Test User");
    await page.getByLabel(/privacy notice/i).check();
    await page.getByRole("button", { name: /Start Test/i }).click();

    await expect(page).toHaveURL(/\/exam\/test/, { timeout: 15000 });
    await expect(page.getByText(/Question 1 of 50/i)).toBeVisible();

    const option = page.locator('label[for="option-A"]').first();
    if (await option.isVisible()) {
      await option.click();
    }

    await page.getByRole("button", { name: /End Test/i }).click();
    await page.getByRole("button", { name: /Submit Test/i }).click();
    await expect(page).toHaveURL(/\/exam\/results/, { timeout: 15000 });
    await expect(page.getByText(/Your Score/i)).toBeVisible();
  });
});

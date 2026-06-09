import { test, expect } from "@playwright/test";

test.describe("Examiner flow", () => {
  test.skip(!process.env.E2E_WITH_API, "Set E2E_WITH_API=1 with backend running");

  test("examiner login shows generic error on invalid credentials", async ({ page }) => {
    await page.goto("/");
    await page.getByText("Login as Examiner").click();
    await page.getByLabel("Username").fill("nonexistent");
    await page.getByLabel("Password").fill("WrongPassword1!");
    await page.getByRole("button", { name: /^Login$/i }).click();
    await expect(page.getByRole("alert")).toContainText(/invalid username or password/i);
  });

  test("examiner dashboard loads after login", async ({ page }) => {
    const username = process.env.E2E_EXAMINER_USER ?? "admin";
    const password = process.env.E2E_EXAMINER_PASSWORD ?? "ChangeMe123456!";

    await page.goto("/");
    await page.getByText("Login as Examiner").click();
    await page.getByLabel("Username").fill(username);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: /^Login$/i }).click();

    await expect(page).toHaveURL(/\/examiner\/dashboard/, { timeout: 15000 });
    await expect(page.getByText(/Question Bank/i)).toBeVisible();
  });
});

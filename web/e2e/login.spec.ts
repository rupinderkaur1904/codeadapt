import { expect, test } from "@playwright/test";

// The test API runs with the dev stub enabled, so the app starts as dev-student. A real
// login session takes precedence over the stub (ADR-029): the cookie, the CSRF token and
// logout are exercised here through the browser and the dev-server proxy.
test("a password login replaces the dev stub until logout", async ({ page }) => {
  await page.goto("/");
  // The intro opens the site once per tab session; Enter continues to the landing page.
  const intro = page.getByRole("button", { name: "Enter CodeAdapt" });
  await expect(intro).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(intro).toHaveCount(0);
  await expect(page.getByText("Development role")).toBeVisible();

  const status = await page.evaluate(async () => {
    const r = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "e2e-researcher", password: "e2e researcher password" }),
    });
    return r.status;
  });
  expect(status).toBe(200);
  // The session cookie is HttpOnly (scripts cannot read it) and scoped to the API.
  const session = (await page.context().cookies()).find((c) => c.name === "codeadapt_session");
  expect(session).toMatchObject({ httpOnly: true, sameSite: "Strict", path: "/api" });

  await page.reload();
  await expect(page.getByText("e2e-researcher")).toBeVisible();
  await expect(page.getByText("Development role")).toHaveCount(0);
  await page.getByRole("link", { name: "Research" }).click();
  await expect(page.getByRole("heading", { name: "Research" })).toBeVisible();

  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page.getByText("Development role")).toBeVisible();
});

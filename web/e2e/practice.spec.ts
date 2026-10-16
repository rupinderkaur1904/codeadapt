import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { expect, test, type Page } from "@playwright/test";

const problemDir = fileURLToPath(new URL("../../content/demo/lower-bound/", import.meta.url));
const read = (rel: string) => readFileSync(problemDir + rel, "utf-8");

async function replaceCode(page: Page, source: string) {
  const editor = page.locator(".cm-content");
  await editor.click();
  await page.keyboard.press("ControlOrMeta+a");
  await page.keyboard.press("Delete");
  // insertText bypasses CodeMirror's auto-indent and bracket closing.
  await page.keyboard.insertText(source);
}

test("student submits, sees diagnosis feedback, fixes the bug and passes", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Lower bound" }).click();
  await expect(page.getByRole("heading", { name: "Lower bound", level: 1 })).toBeVisible();

  await replaceCode(page, read("error_models/hi_init_last_index.cpp"));
  await page.getByRole("button", { name: "Submit" }).click();
  const feedback = page.getByTestId("feedback");
  await expect(feedback).toContainText("Can your search ever return a.size()?");
  await expect(feedback).toContainText("The target is larger than every element.");
  // Internal labels never reach the student.
  await expect(page.locator("body")).not.toContainText("hi_init_last_index");
  // The adaptive policy recommends another problem that probes the same skill.
  const next = page.getByRole("complementary", { name: "Recommended next" });
  await expect(next.getByRole("link", { name: "Go to Count occurrences" })).toBeVisible();

  await replaceCode(page, read("reference.cpp"));
  await page.getByRole("button", { name: "Submit" }).click();
  await expect(feedback).toContainText("passed all 17 tests");
  await expect(page.getByText("17/17 tests passed")).toBeVisible();
  await expect(next).toContainText("Your last attempt passed every test.");

  await next.getByRole("link", { name: "Go to Count occurrences" }).click();
  await expect(page.getByRole("heading", { name: "Count occurrences", level: 1 })).toBeVisible();
});

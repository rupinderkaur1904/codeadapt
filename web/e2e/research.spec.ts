import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { expect, test } from "@playwright/test";

const problemDir = fileURLToPath(new URL("../../content/demo/lower-bound/", import.meta.url));
const read = (rel: string) => readFileSync(problemDir + rel, "utf-8");

// The researcher half of the loop: a submission's trace and the researcher-only learner model,
// through the real API, worker and sandbox. Synthetic programs (ADR-008); this checks the
// mechanism, not accuracy.
test("researcher follows a submission to its trace and the learner model", async ({ page }) => {
  // The landing page leads to the problem list (frontend theme, routes from branch 9vflva).
  await page.goto("/");
  // The intro opens the site once per tab session; a click anywhere continues.
  const intro = page.getByRole("button", { name: "Enter CodeAdapt" });
  await intro.click();
  await expect(intro).toHaveCount(0);
  await page.getByRole("link", { name: "Start digging" }).click();
  await expect(page).toHaveURL(/\/problems$/);
  await page.getByRole("link", { name: "Lower bound" }).click();
  const editor = page.locator(".cm-content");
  await editor.click();
  await page.keyboard.press("ControlOrMeta+a");
  await page.keyboard.press("Delete");
  await page.keyboard.insertText(read("error_models/exact_match_sentinel.cpp"));
  await page.getByRole("button", { name: "Submit" }).click();
  await expect(page.getByTestId("feedback")).toContainText(
    "Re-read what should be returned when the target is not in the array.",
  );
  // Students never see learner-model output or internal labels.
  await expect(page.locator("body")).not.toContainText("exact_match_sentinel");
  await expect(page.locator("body")).not.toContainText("P(known)");

  // The student's own history lists the attempt, still without internal labels.
  await page.getByRole("link", { name: "My attempts" }).click();
  await expect(page.getByRole("heading", { name: "My attempts" })).toBeVisible();
  await expect(page.getByRole("row").filter({ hasText: "Lower bound" }).first()).toBeVisible();
  await expect(page.locator("body")).not.toContainText("exact_match_sentinel");

  await page.getByLabel("Development role").selectOption("researcher");
  await page.getByRole("link", { name: "Research" }).click();
  await expect(page.getByRole("heading", { name: "Research" })).toBeVisible();
  const row = page.getByRole("row").filter({ hasText: "exact_match_sentinel" });
  await expect(row).toHaveCount(1);
  await expect(row).toContainText("hypothesis_supported");

  await row.getByRole("link").first().click();
  await expect(page.getByRole("heading", { name: "Submission trace" })).toBeVisible();
  await expect(page.locator("body")).toContainText("fingerprint_consistency");
  await expect(page.locator("body")).toContainText("exact_match_sentinel");
  await expect(page.getByRole("heading", { name: "Adaptation" })).toBeVisible();

  // Reach the learner model through the Learners list.
  await page.getByRole("link", { name: "Learners" }).click();
  await expect(page.getByRole("heading", { name: "Learners" })).toBeVisible();
  await page.getByRole("link", { name: "dev-student" }).click();
  await expect(page.getByRole("heading", { name: "Learner model: dev-student" })).toBeVisible();
  await expect(page.locator("body")).toContainText("estimated under assumed parameters");
  // The named diagnosis is an incorrect observation on its model's skill.
  const skill = page.getByRole("region", { name: "problem_specification" });
  await expect(skill.getByRole("cell", { name: "incorrect" }).first()).toBeVisible();
});

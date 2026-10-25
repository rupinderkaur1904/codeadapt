import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 240_000,
  expect: { timeout: 180_000 },
  retries: 0,
  // One API worker processes every submission in order. Specs running in parallel queue
  // behind each other's jobs (including first-time fingerprinting), so a spec's wait depends
  // on the others; run them one at a time instead.
  workers: 1,
  reporter: [["list"]],
  use: { baseURL: "http://127.0.0.1:4173", trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "./e2e/backend.sh",
      url: "http://127.0.0.1:8000/api/v1/health",
      timeout: 120_000,
      reuseExistingServer: false,
    },
    {
      command: "npm run build && npx vite preview --host 127.0.0.1 --port 4173 --strictPort",
      url: "http://127.0.0.1:4173",
      timeout: 120_000,
      reuseExistingServer: false,
    },
  ],
});

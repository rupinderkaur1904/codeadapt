/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const apiTarget = process.env.CODEADAPT_API_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  // The lazily loaded editor chunk (CodeMirror) is ~650 kB minified, ~210 kB gzipped.
  build: { chunkSizeWarningLimit: 800 },
  server: { proxy: { "/api": apiTarget } },
  preview: { proxy: { "/api": apiTarget } },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
  },
});

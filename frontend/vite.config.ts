import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@brand": path.resolve(__dirname, "../_bmad-output/branding"),
    },
  },
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    css: false,
    globals: true,
    testTimeout: 120000, // E2E tests need longer timeout (2 minutes)
    hookTimeout: 30000, // Test hooks timeout (30 seconds)
    pool: "forks",
    poolOptions: {
      forks: {
        maxForks: 2,
      },
    },
  },
});

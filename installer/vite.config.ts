import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// See https://tauri.app/develop/#vite for why dev server settings are fixed
// like this: Tauri needs a predictable, non-conflicting port and to ignore
// its own Rust source changes so `cargo` (not Vite) handles those reloads.
export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    watch: {
      ignored: ["**/src-tauri/**"],
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  test: {
    environment: "node",
    include: ["tests/**/*.test.ts"],
  },
});

import { resolve } from "node:path";

import { defineConfig } from "vite";

export default defineConfig({
  publicDir: false,
  build: {
    lib: {
      entry: resolve(import.meta.dirname, "src/index.ts"),
      formats: ["cjs"],
      fileName: "index.cjs",
    },
    rollupOptions: {
      external: ["commander"],
      output: {
        banner: "#!/usr/bin/env node",
      },
    },
  },
});

import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig } from "vite";

const projectDir = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  publicDir: false,
  build: {
    lib: {
      entry: resolve(projectDir, "src/index.ts"),
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

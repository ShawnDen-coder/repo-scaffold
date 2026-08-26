import react from "@vitejs/plugin-react";
import dts from "vite-plugin-dts";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), dts({ rollupTypes: true })],
  build: {
    lib: { entry: "src/index.ts", formats: ["es"], fileName: "index" },
    rollupOptions: { external: ["react", "react-dom"] },
  },
});

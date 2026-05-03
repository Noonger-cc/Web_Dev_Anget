import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 80,
    proxy: {
      "/api": {
        target: "http://server-go:8080",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://server-go:8080",
        ws: true,
      },
    },
  },
});

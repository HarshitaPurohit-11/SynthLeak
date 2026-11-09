/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev the browser talks to Vite, and Vite proxies REST + WebSocket to the FastAPI backend.
// That avoids CORS (the contract does not require the backend to enable it).
// Override the target with: BACKEND_URL=http://host:8000 npm run dev
const backend = process.env.BACKEND_URL ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/health": backend,
      "/pipelines": backend,
      "/alerts": backend,
      "/tickets": backend,
      "/ws": { target: backend, ws: true, changeOrigin: true },
    },
  },
  preview: { port: 3000 },
  test: { environment: "node", include: ["src/**/*.test.ts"] },
});

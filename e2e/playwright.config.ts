import { defineConfig } from "@playwright/test";
import { existsSync, mkdirSync, rmSync } from "node:fs";
import path from "node:path";

const raiz = path.resolve(__dirname, "..");
const tmp = path.join(__dirname, ".tmp");
if (!process.env.TEST_WORKER_INDEX) {
  rmSync(tmp, { recursive: true, force: true }); // banco e fotos novos a cada execução (só no processo principal)
  mkdirSync(tmp, { recursive: true });
}

const venv = path.join(raiz, "backend", ".venv");
const python = existsSync(path.join(venv, "Scripts", "python.exe"))
  ? path.join(venv, "Scripts", "python.exe")
  : path.join(venv, "bin", "python");

const API = "http://127.0.0.1:8100";
const WEB = "http://localhost:5180";

export default defineConfig({
  testDir: "./tests",
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [["list"]],
  use: { baseURL: WEB, viewport: { width: 1280, height: 900 }, locale: "pt-BR" },
  webServer: [
    {
      command: `"${python}" -m uvicorn app.main:app --host 127.0.0.1 --port 8100`,
      cwd: path.join(raiz, "backend"),
      url: `${API}/api/v1/health`,
      reuseExistingServer: false,
      env: {
        DATABASE_URL: `sqlite:///${path.join(tmp, "e2e.db").replace(/\\/g, "/")}`,
        FOTOS_DIR: path.join(tmp, "fotos"),
        INSPECOES_HOJE: "2026-10-23",
      },
    },
    {
      command: "npx vite --port 5180 --strictPort",
      cwd: path.join(raiz, "frontend"),
      url: WEB,
      reuseExistingServer: false,
      env: { API_URL: API },
    },
  ],
});

/**
 * Dev server proxy: lee BACKEND_URL del .env en la raíz del repo (no versionar).
 * Angular llama a /api/... y esto reenvía al FastAPI.
 */
const fs = require("fs");
const path = require("path");

function loadEnvFile(absPath) {
  const env = {};
  if (!fs.existsSync(absPath)) return env;
  for (const line of fs.readFileSync(absPath, "utf8").split(/\r?\n/)) {
    if (!line || line.trim().startsWith("#")) continue;
    const eq = line.indexOf("=");
    if (eq < 1) continue;
    const key = line.slice(0, eq).trim();
    let val = line.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    env[key] = val;
  }
  return env;
}

const repoRoot = path.resolve(__dirname, "..");
const rootEnv = loadEnvFile(path.join(repoRoot, ".env"));
const target = (process.env.BACKEND_URL || rootEnv.BACKEND_URL || "").trim();
if (!target) {
  throw new Error(
    "proxy.conf.js: definí BACKEND_URL en el archivo .env de la raíz del repositorio " +
      "(o exportá process.env.BACKEND_URL). Ej.: BACKEND_URL=http://127.0.0.1:8000",
  );
}

module.exports = {
  "/api": {
    target,
    secure: false,
    changeOrigin: true,
    ws: true,   // permite upgrade WebSocket para /api/ws/...
  },
};

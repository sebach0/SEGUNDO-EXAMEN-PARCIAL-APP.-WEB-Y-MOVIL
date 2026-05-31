/**
 * Lee MAILHOG_WEB_URL del `.env` en la raíz del repo y genera
 * `src/environments/mailhog-url.generated.ts` (sin URLs fijas en environment.ts).
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

const frontendDir = path.resolve(__dirname, "..");
const repoRoot = path.resolve(frontendDir, "..");
const envPath = path.join(repoRoot, ".env");
const rootEnv = loadEnvFile(envPath);

// Docker build: el contexto suele ser solo `frontend/` → no hay `.env` del monorepo;
// Compose pasa MAILHOG_WEB_URL como build-arg (vacío en prod está bien).
const hasBuildEnv =
  Object.prototype.hasOwnProperty.call(process.env, "MAILHOG_WEB_URL") &&
  process.env.MAILHOG_WEB_URL !== undefined;

let raw;
if (hasBuildEnv) {
  raw = String(process.env.MAILHOG_WEB_URL).trim();
} else {
  if (!Object.prototype.hasOwnProperty.call(rootEnv, "MAILHOG_WEB_URL")) {
    throw new Error(
      "[sync-from-root-env] Falta MAILHOG_WEB_URL: definila en " +
        envPath +
        " (clave MAILHOG_WEB_URL=...) o exportá MAILHOG_WEB_URL antes del build (Docker: build-arg). Podés dejarla vacía: MAILHOG_WEB_URL=",
    );
  }
  raw = String(rootEnv.MAILHOG_WEB_URL ?? "").trim();
}

const outPath = path.join(frontendDir, "src", "environments", "mailhog-url.generated.ts");
const body = `/* Archivo generado por scripts/sync-from-root-env.cjs — no editar a mano. */
export const mailhogWebUrl = ${JSON.stringify(raw)};
`;
fs.writeFileSync(outPath, body, "utf8");

import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const windowsMountedPath = /^\/mnt\/[a-z]\//i;
const safeTmpDir = "/tmp";
const env = { ...process.env };

if (process.platform !== "win32") {
  for (const key of ["TMPDIR", "TMP", "TEMP"]) {
    if (!env[key] || windowsMountedPath.test(env[key])) {
      env[key] = safeTmpDir;
    }
  }
}

const scriptsDir = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(scriptsDir, "..");
const vitestPackageJson = require.resolve("vitest/package.json");
const vitestEntry = path.join(path.dirname(vitestPackageJson), "vitest.mjs");
const result = spawnSync(process.execPath, [vitestEntry, "run", ...process.argv.slice(2)], {
  cwd: webRoot,
  env,
  stdio: "inherit",
});

if (result.error) {
  throw result.error;
}

process.exit(result.status ?? 1);

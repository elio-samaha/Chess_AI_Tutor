import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const WINDOWS_MOUNT_PATH = /^\/mnt\/[a-z]\//i;
const SAFE_TMP_DIR = "/tmp";

if (process.platform !== "win32") {
  if (!process.env.TMPDIR || WINDOWS_MOUNT_PATH.test(process.env.TMPDIR)) {
    process.env.TMPDIR = SAFE_TMP_DIR;
  }
  if (!process.env.TMP || WINDOWS_MOUNT_PATH.test(process.env.TMP)) {
    process.env.TMP = SAFE_TMP_DIR;
  }
  if (!process.env.TEMP || WINDOWS_MOUNT_PATH.test(process.env.TEMP)) {
    process.env.TEMP = SAFE_TMP_DIR;
  }
}

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["src/test/setup.ts"],
  },
});

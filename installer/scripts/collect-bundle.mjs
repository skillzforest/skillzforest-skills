#!/usr/bin/env node
// Copies whatever `tauri build` just produced into the repo-wide
// dist/installer/<os>/ layout, so skill/pack artifacts (dist/skills/,
// dist/packs/) and app artifacts never share a folder. Run after
// `tauri build` — see package.json's "installer:build" script.
import { existsSync, mkdirSync, readdirSync, copyFileSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const installerRoot = join(__dirname, "..");
const repoRoot = join(installerRoot, "..");
const bundleRoot = join(installerRoot, "src-tauri", "target", "release", "bundle");

const OS_DIR = { darwin: "macos", win32: "windows", linux: "linux" }[process.platform];
if (!OS_DIR) {
  console.error(`Unrecognized platform '${process.platform}' — nothing collected.`);
  process.exit(1);
}

const FORMATS_BY_PLATFORM = {
  darwin: ["dmg", "macos"],
  win32: ["nsis", "msi"],
  linux: ["appimage", "deb", "rpm"],
};

if (!existsSync(bundleRoot)) {
  console.error(`No bundle output found at ${bundleRoot} — did 'tauri build' run first?`);
  process.exit(1);
}

const destDir = join(repoRoot, "dist", "installer", OS_DIR);
mkdirSync(destDir, { recursive: true });

let copied = 0;
for (const format of FORMATS_BY_PLATFORM[process.platform]) {
  const formatDir = join(bundleRoot, format);
  if (!existsSync(formatDir)) continue;
  for (const entry of readdirSync(formatDir)) {
    const src = join(formatDir, entry);
    if (statSync(src).isDirectory()) continue; // skip e.g. the unpacked .app bundle dir itself on some formats
    const dest = join(destDir, entry);
    copyFileSync(src, dest);
    console.log(`Copied ${format}/${entry} -> dist/installer/${OS_DIR}/${entry}`);
    copied++;
  }
}

if (copied === 0) {
  console.warn(`No installer artifacts found under ${bundleRoot} for platform '${process.platform}'.`);
}

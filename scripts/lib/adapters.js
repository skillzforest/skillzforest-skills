// One adapter per runtime.json "installStrategy". Each adapter takes a
// skill's canonical source folder and writes a distribution for one runtime.
// Adapters never read from or write back into skills/ — only from the
// source dir (read-only) into an output dir under dist/.
const fs = require('fs');
const path = require('path');
const AdmZip = require('adm-zip');
const { EXCLUDED_FROM_DIST } = require('./skills');

function copyDir(srcDir, destDir) {
  fs.mkdirSync(destDir, { recursive: true });
  for (const entry of fs.readdirSync(srcDir, { withFileTypes: true })) {
    if (EXCLUDED_FROM_DIST.has(entry.name)) continue;
    const src = path.join(srcDir, entry.name);
    const dest = path.join(destDir, entry.name);
    if (entry.isDirectory()) {
      copyDir(src, dest);
    } else {
      fs.copyFileSync(src, dest);
    }
  }
}

function addDirToZip(zip, dir, zipBasePath) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (EXCLUDED_FROM_DIST.has(entry.name)) continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      addDirToZip(zip, fullPath, path.join(zipBasePath, entry.name));
    } else {
      zip.addLocalFile(fullPath, zipBasePath);
    }
  }
}

// installStrategy: "filesystem" — the runtime reads a plain folder from disk
// (e.g. ~/.claude/skills/<name>/, ~/.agents/skills/<name>/). No transformation.
function adaptFilesystem(skill, outDir, _runtime) {
  copyDir(skill.dir, outDir);
  return { files: listFiles(outDir) };
}

// installStrategy: "upload" — the runtime imports a zip (e.g. Claude.ai's
// custom Skills upload). Mirrors the historical *.skill format: contents
// nested one level under the skill id inside the zip.
function adaptUpload(skill, outDir, _runtime) {
  fs.mkdirSync(outDir, { recursive: true });
  const version = (skill.manifest && skill.manifest.version) || '0.0.0';
  const zip = new AdmZip();
  addDirToZip(zip, skill.dir, skill.name);
  const zipPath = path.join(outDir, `${skill.name}-${version}.skill`);
  zip.writeZip(zipPath);
  return { files: [path.relative(outDir, zipPath)] };
}

// installStrategy: "manual-bundle" — for runtimes with no file-based skill
// loading at all (e.g. a chat product's "custom instructions"). Produces one
// self-contained, copy-pasteable Markdown file: SKILL.md's content plus a
// short header telling the user where to paste it. This is a real,
// deterministic transformation (not a native integration) — it's what makes
// the skill "usable" on a runtime that has no install mechanism to hook into.
function adaptManualBundle(skill, outDir, runtime) {
  fs.mkdirSync(outDir, { recursive: true });
  const version = (skill.manifest && skill.manifest.version) || '0.0.0';
  const skillMd = fs.readFileSync(path.join(skill.dir, 'SKILL.md'), 'utf8');
  const name = (skill.manifest && skill.manifest.name) || skill.name;
  const header = [
    `# ${name} — for ${runtime.name}`,
    '',
    `This runtime has no native skill/plugin loading mechanism (see runtimes/${runtime.id}/README.md).`,
    `Copy everything below into ${runtime.name}'s custom instructions / system prompt to use this skill there.`,
    '',
    '---',
    '',
  ].join('\n');
  const bundlePath = path.join(outDir, `${skill.name}-${version}.md`);
  fs.writeFileSync(bundlePath, header + skillMd);
  return { files: [path.relative(outDir, bundlePath)] };
}

function listFiles(dir, base = dir) {
  let out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (EXCLUDED_FROM_DIST.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      out = out.concat(listFiles(full, base));
    } else {
      out.push(path.relative(base, full));
    }
  }
  return out;
}

// No adapter is registered for "plugin" or "manual" — those require a real,
// verified integration (e.g. a ChatGPT plugin manifest) that doesn't exist
// yet. Registering a fake one would fabricate a distribution that was never
// built for that mechanism.
const ADAPTERS = {
  filesystem: adaptFilesystem,
  upload: adaptUpload,
  'manual-bundle': adaptManualBundle,
};

module.exports = { ADAPTERS, copyDir, listFiles };

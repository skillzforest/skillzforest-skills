#!/usr/bin/env node
// Validates skills/, packs/, and runtimes/. Read-only — never modifies sources.
const fs = require('fs');
const path = require('path');
const {
  REPO_ROOT,
  SKILLS_ROOT,
  listFamilies,
  listPacks,
  readPack,
  listRuntimes,
  readRuntime,
  COMPATIBILITY_STATUSES,
} = require('./lib/skills');

const errors = [];
const warnings = [];

function checkSkillFolders() {
  const seenNames = new Map(); // name -> family
  const seenIds = new Map(); // skill.json id -> name
  for (const family of listFamilies()) {
    const familyDir = path.join(SKILLS_ROOT, family);
    for (const entry of fs.readdirSync(familyDir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const skillDir = path.join(familyDir, entry.name);
      const label = `skills/${family}/${entry.name}`;

      if (!fs.existsSync(path.join(skillDir, 'SKILL.md'))) {
        errors.push(`${label} has no SKILL.md`);
        continue;
      }
      if (!entry.name.startsWith(`${family}-`)) {
        errors.push(`${label} does not use the '${family}-' prefix expected for this category`);
      }
      if (seenNames.has(entry.name)) {
        errors.push(`skill '${entry.name}' is duplicated: skills/${seenNames.get(entry.name)}/${entry.name} and ${label}`);
      } else {
        seenNames.set(entry.name, family);
      }

      const manifestPath = path.join(skillDir, 'skill.json');
      if (!fs.existsSync(manifestPath)) {
        errors.push(`${label} has no skill.json`);
        continue;
      }
      let manifest;
      try {
        manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
      } catch (e) {
        errors.push(`${label}/skill.json is not valid JSON: ${e.message}`);
        continue;
      }
      if (manifest.id !== entry.name) {
        errors.push(`${label}/skill.json id '${manifest.id}' does not match its folder name`);
      }
      if (seenIds.has(manifest.id)) {
        errors.push(`skill.json id '${manifest.id}' is duplicated (also used by ${seenIds.get(manifest.id)})`);
      } else {
        seenIds.set(manifest.id, label);
      }
      for (const [runtimeId, status] of Object.entries(manifest.compatibility || {})) {
        if (!COMPATIBILITY_STATUSES.includes(status)) {
          errors.push(`${label}/skill.json declares invalid compatibility status '${status}' for '${runtimeId}'`);
        }
        if (!listRuntimes().includes(runtimeId)) {
          errors.push(`${label}/skill.json declares compatibility with unknown runtime '${runtimeId}' (no runtimes/${runtimeId}/runtime.json)`);
        }
      }
    }
  }
  return seenNames;
}

function checkPacks(knownSkills) {
  for (const id of listPacks()) {
    const pack = readPack(id);
    for (const skillName of pack.skills || []) {
      if (!knownSkills.has(skillName)) {
        errors.push(`packs/${id}/pack.json references unknown skill '${skillName}'`);
      }
    }
    const packDir = path.join(REPO_ROOT, 'packs', id);
    for (const entry of fs.readdirSync(packDir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const nested = path.join(packDir, entry.name);
      if (fs.existsSync(path.join(nested, 'SKILL.md'))) {
        errors.push(`packs/${id}/${entry.name} embeds a skill copy — packs must only reference skills/`);
      }
    }
  }
}

const RUNTIME_STATUSES = ['verified', 'supported', 'unknown'];

function checkRuntimes() {
  for (const id of listRuntimes()) {
    const runtime = readRuntime(id);
    if (runtime.id !== id) {
      errors.push(`runtimes/${id}/runtime.json id '${runtime.id}' does not match its folder name`);
    }
    if (!runtime.installStrategy) {
      errors.push(`runtimes/${id}/runtime.json is missing installStrategy`);
    }
    if (runtime.status && !RUNTIME_STATUSES.includes(runtime.status)) {
      errors.push(`runtimes/${id}/runtime.json declares invalid status '${runtime.status}'`);
    }
    if (runtime.installStrategy === 'filesystem' && !(runtime.paths && runtime.paths.user)) {
      errors.push(`runtimes/${id}/runtime.json uses installStrategy 'filesystem' but declares no paths.user`);
    }
  }
}

function checkDistIsGenerated() {
  const gitignore = path.join(REPO_ROOT, '.gitignore');
  if (!fs.existsSync(gitignore) || !fs.readFileSync(gitignore, 'utf8').includes('dist/')) {
    warnings.push('dist/ is not git-ignored — build artifacts should never be committed as a second source of truth');
  }
  // dist/ never diverges manually from source: it must only ever be
  // produced by scripts/build-*.js, so it must not exist as a tracked
  // path skills/packs/runtimes read from. There's nothing else to check
  // statically here beyond keeping dist/ out of version control.
}

const knownSkills = checkSkillFolders();
checkPacks(knownSkills);
checkRuntimes();
checkDistIsGenerated();

console.log(
  `Checked ${knownSkills.size} skill(s) across ${listFamilies().length} categories, ` +
  `${listPacks().length} pack(s), ${listRuntimes().length} runtime(s).`
);

if (warnings.length) {
  console.warn('\nWarnings:');
  for (const w of warnings) console.warn(`  - ${w}`);
}

if (errors.length) {
  console.error('\nErrors:');
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}

console.log('All skills, packs, and runtimes are valid.');

#!/usr/bin/env node
// Validates skills/, packs/, and runtimes/. Read-only — never modifies sources.
const fs = require('fs');
const path = require('path');
const {
  REPO_ROOT,
  SKILLS_ROOT,
  listFamilies,
  listStandaloneSkillNames,
  listDomains,
  findDomain,
  prefixOf,
  listPacks,
  readPack,
  listRuntimes,
  readRuntime,
  COMPATIBILITY_STATUSES,
} = require('./lib/skills');

const errors = [];
const warnings = [];

// Validates one skill folder (SKILL.md presence, prefix, skill.json,
// duplicate name/id, compatibility values) and records it into seenNames /
// seenIds. Shared by the flat-domain, subcategory, and standalone cases
// below so the three don't drift from each other.
function checkOneSkill({ skillDir, label, name, allowedPrefixes, groupKey, requireManifest, seenNames, seenIds }) {
  if (!fs.existsSync(path.join(skillDir, 'SKILL.md'))) {
    errors.push(`${label} has no SKILL.md`);
    return;
  }
  if (allowedPrefixes) {
    const prefix = prefixOf(name);
    if (!allowedPrefixes.includes(prefix)) {
      errors.push(
        `${label} uses prefix '${prefix}-' which is not registered for this location `
        + `(skills/domains.json lists: ${allowedPrefixes.map((p) => `${p}-`).join(', ')})`
      );
    }
  }
  if (seenNames.has(name)) {
    errors.push(`skill '${name}' is duplicated: skills/${seenNames.get(name)}/${name} and ${label}`);
  } else {
    seenNames.set(name, groupKey);
  }

  const manifestPath = path.join(skillDir, 'skill.json');
  if (!fs.existsSync(manifestPath)) {
    if (requireManifest) errors.push(`${label} has no skill.json`);
    return;
  }
  let manifest;
  try {
    manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  } catch (e) {
    errors.push(`${label}/skill.json is not valid JSON: ${e.message}`);
    return;
  }
  if (manifest.id !== name) {
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

function checkSkillFolders() {
  const seenNames = new Map(); // name -> domain (or domain/subcategory, or '(standalone)')
  const seenIds = new Map(); // skill.json id -> label
  const domains = listDomains();
  if (domains.length === 0) {
    errors.push('skills/domains.json is missing or declares no domains');
  }

  for (const domain of listFamilies()) {
    const domainDir = path.join(SKILLS_ROOT, domain);
    const domainEntry = findDomain(domain);
    if (!domainEntry) {
      errors.push(`skills/${domain} has no matching entry in skills/domains.json — add one, or move its skills under a registered domain`);
    }

    if (domainEntry && domainEntry.subcategories) {
      const declaredSubIds = new Set(domainEntry.subcategories.map((s) => s.id));
      for (const subEntry of fs.readdirSync(domainDir, { withFileTypes: true })) {
        if (!subEntry.isDirectory()) continue;
        const subDir = path.join(domainDir, subEntry.name);
        const subcategoryEntry = domainEntry.subcategories.find((s) => s.id === subEntry.name);
        if (!subcategoryEntry) {
          errors.push(`skills/${domain}/${subEntry.name} has no matching subcategory in skills/domains.json (declared: ${[...declaredSubIds].join(', ')})`);
        }
        for (const entry of fs.readdirSync(subDir, { withFileTypes: true })) {
          if (!entry.isDirectory()) continue;
          checkOneSkill({
            skillDir: path.join(subDir, entry.name),
            label: `skills/${domain}/${subEntry.name}/${entry.name}`,
            name: entry.name,
            allowedPrefixes: subcategoryEntry ? subcategoryEntry.prefixes : null,
            groupKey: `${domain}/${subEntry.name}`,
            requireManifest: true,
            seenNames,
            seenIds,
          });
        }
      }
      continue;
    }

    for (const entry of fs.readdirSync(domainDir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      checkOneSkill({
        skillDir: path.join(domainDir, entry.name),
        label: `skills/${domain}/${entry.name}`,
        name: entry.name,
        allowedPrefixes: domainEntry ? domainEntry.prefixes : null,
        groupKey: domain,
        requireManifest: true,
        seenNames,
        seenIds,
      });
    }
  }

  // Standalone skills (skills/<name>/SKILL.md, no domain/prefix): generic
  // agent-tooling skills that aren't part of the domain/pack/runtime
  // distribution system. They still need a unique name and, if present, a
  // consistent skill.json, but no domain prefix and no skill.json is required.
  for (const name of listStandaloneSkillNames()) {
    checkOneSkill({
      skillDir: path.join(SKILLS_ROOT, name),
      label: `skills/${name}`,
      name,
      allowedPrefixes: null,
      groupKey: '(standalone)',
      requireManifest: false,
      seenNames,
      seenIds,
    });
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
  `Checked ${knownSkills.size} skill(s) across ${listFamilies().length} domain(s), ` +
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

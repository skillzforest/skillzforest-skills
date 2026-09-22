const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.join(__dirname, '..', '..');
const SKILLS_ROOT = path.join(REPO_ROOT, 'skills');
const PACKS_ROOT = path.join(REPO_ROOT, 'packs');
const RUNTIMES_ROOT = path.join(REPO_ROOT, 'runtimes');
const DIST_ROOT = path.join(REPO_ROOT, 'dist');

// Files/dirs never copied into a generated distribution.
const EXCLUDED_FROM_DIST = new Set(['node_modules', 'out', '.DS_Store']);

// Directories that never contain a skill or family (helpers, not categories).
const NON_FAMILY_DIRS = new Set(['lib']);

const COMPATIBILITY_STATUSES = ['native', 'supported', 'adapted', 'unsupported', 'unknown'];

const DOMAINS_FILE = path.join(SKILLS_ROOT, 'domains.json');

// skills/domains.json is the buyer-facing category grouping: each domain is
// a folder under skills/ (e.g. 'sales') and accepts one or more technical id
// prefixes (e.g. 'av'), either directly or split into named subcategories
// one folder level deeper (e.g. 'development' -> 'code', 'ux-ui', 'seo').
// A domain (or subcategory) can accept several prefixes (e.g.
// 'project-management' accepts both 'board' and 'docs') — this is what
// replaced the old one-folder-per-prefix "family" convention.
function listDomains() {
  if (!fs.existsSync(DOMAINS_FILE)) return [];
  return JSON.parse(fs.readFileSync(DOMAINS_FILE, 'utf8')).domains || [];
}

function findDomain(domainId) {
  return listDomains().find((d) => d.id === domainId) || null;
}

// The prefix a skill id declares, e.g. 'av-devis' -> 'av'.
function prefixOf(skillName) {
  return skillName.split('-')[0];
}

// A directory directly under skills/ that itself has a SKILL.md is a
// standalone skill (no family, no prefix, no skill.json requirement) —
// e.g. skills/github-issue-context/. It is not a family and its
// subdirectories (scripts/, references/, ...) are never scanned for
// further skills.
function isStandaloneSkillDir(dir) {
  return fs.existsSync(path.join(dir, 'SKILL.md'));
}

function listFamilies() {
  if (!fs.existsSync(SKILLS_ROOT)) return [];
  return fs.readdirSync(SKILLS_ROOT, { withFileTypes: true })
    .filter((d) => d.isDirectory() && !NON_FAMILY_DIRS.has(d.name))
    .filter((d) => !isStandaloneSkillDir(path.join(SKILLS_ROOT, d.name)))
    .map((d) => d.name);
}

function listStandaloneSkillNames() {
  if (!fs.existsSync(SKILLS_ROOT)) return [];
  return fs.readdirSync(SKILLS_ROOT, { withFileTypes: true })
    .filter((d) => d.isDirectory() && !NON_FAMILY_DIRS.has(d.name))
    .filter((d) => isStandaloneSkillDir(path.join(SKILLS_ROOT, d.name)))
    .map((d) => d.name);
}

function readSkillJson(dir) {
  const p = path.join(dir, 'skill.json');
  return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : null;
}

// Returns [{ name, domain, subcategory, dir, manifest }] for every skill
// folder that has a SKILL.md. `domain` is the skills/<domain>/ folder name
// (e.g. 'sales'), or null for a standalone skill (one with no domain/prefix,
// living directly under skills/<name>/). `subcategory` is the
// skills/<domain>/<subcategory>/ folder name for a domain that declares
// subcategories in domains.json (e.g. 'development' -> 'code'), else null.
function listSkills() {
  const skills = [];
  for (const domain of listFamilies()) {
    const domainDir = path.join(SKILLS_ROOT, domain);
    const domainEntry = findDomain(domain);
    if (domainEntry && domainEntry.subcategories) {
      for (const subEntry of fs.readdirSync(domainDir, { withFileTypes: true })) {
        if (!subEntry.isDirectory()) continue;
        const subDir = path.join(domainDir, subEntry.name);
        for (const entry of fs.readdirSync(subDir, { withFileTypes: true })) {
          if (!entry.isDirectory()) continue;
          const dir = path.join(subDir, entry.name);
          if (fs.existsSync(path.join(dir, 'SKILL.md'))) {
            skills.push({ name: entry.name, domain, subcategory: subEntry.name, dir, manifest: readSkillJson(dir) });
          }
        }
      }
      continue;
    }
    for (const entry of fs.readdirSync(domainDir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const dir = path.join(domainDir, entry.name);
      if (fs.existsSync(path.join(dir, 'SKILL.md'))) {
        skills.push({ name: entry.name, domain, subcategory: null, dir, manifest: readSkillJson(dir) });
      }
    }
  }
  for (const name of listStandaloneSkillNames()) {
    const dir = path.join(SKILLS_ROOT, name);
    skills.push({ name, domain: null, subcategory: null, dir, manifest: readSkillJson(dir) });
  }
  return skills;
}

function findSkill(name) {
  return listSkills().find((s) => s.name === name) || null;
}

function findSkillDir(name) {
  const match = findSkill(name);
  return match ? match.dir : null;
}

function listPacks() {
  if (!fs.existsSync(PACKS_ROOT)) return [];
  return fs.readdirSync(PACKS_ROOT, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .filter((id) => fs.existsSync(path.join(PACKS_ROOT, id, 'pack.json')));
}

function readPack(id) {
  const packPath = path.join(PACKS_ROOT, id, 'pack.json');
  return JSON.parse(fs.readFileSync(packPath, 'utf8'));
}

function listRuntimes() {
  if (!fs.existsSync(RUNTIMES_ROOT)) return [];
  return fs.readdirSync(RUNTIMES_ROOT, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .filter((id) => fs.existsSync(path.join(RUNTIMES_ROOT, id, 'runtime.json')));
}

function readRuntime(id) {
  const runtimePath = path.join(RUNTIMES_ROOT, id, 'runtime.json');
  if (!fs.existsSync(runtimePath)) return null;
  return JSON.parse(fs.readFileSync(runtimePath, 'utf8'));
}

module.exports = {
  REPO_ROOT,
  SKILLS_ROOT,
  PACKS_ROOT,
  RUNTIMES_ROOT,
  DIST_ROOT,
  EXCLUDED_FROM_DIST,
  COMPATIBILITY_STATUSES,
  listFamilies,
  listStandaloneSkillNames,
  listDomains,
  findDomain,
  prefixOf,
  listSkills,
  findSkill,
  findSkillDir,
  listPacks,
  readPack,
  listRuntimes,
  readRuntime,
};

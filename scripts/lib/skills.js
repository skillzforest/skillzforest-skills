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

function listFamilies() {
  if (!fs.existsSync(SKILLS_ROOT)) return [];
  return fs.readdirSync(SKILLS_ROOT, { withFileTypes: true })
    .filter((d) => d.isDirectory() && !NON_FAMILY_DIRS.has(d.name))
    .map((d) => d.name);
}

function readSkillJson(dir) {
  const p = path.join(dir, 'skill.json');
  return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : null;
}

// Returns [{ name, family, dir, manifest }] for every skill folder that has a SKILL.md.
function listSkills() {
  const skills = [];
  for (const family of listFamilies()) {
    const familyDir = path.join(SKILLS_ROOT, family);
    for (const entry of fs.readdirSync(familyDir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const dir = path.join(familyDir, entry.name);
      if (fs.existsSync(path.join(dir, 'SKILL.md'))) {
        skills.push({ name: entry.name, family, dir, manifest: readSkillJson(dir) });
      }
    }
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
  listSkills,
  findSkill,
  findSkillDir,
  listPacks,
  readPack,
  listRuntimes,
  readRuntime,
};

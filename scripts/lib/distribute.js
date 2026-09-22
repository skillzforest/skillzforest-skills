// Builds one skill's distribution for one runtime: skills/<f>/<name>/ -> dist/skills/<name>/<runtime>/
// Never modifies skills/, packs/, or runtimes/ — only ever writes under dist/.
const fs = require('fs');
const path = require('path');
const { DIST_ROOT, findSkill, readRuntime } = require('./skills');
const { ADAPTERS } = require('./adapters');

const COMPATIBLE_STATUSES = new Set(['native', 'supported', 'adapted']);

// Returns { status: 'built', path } | { status: 'skipped', reason }
function buildSkillForRuntime(skillName, runtimeId, opts = {}) {
  const skill = findSkill(skillName);
  if (!skill) return { status: 'skipped', reason: `unknown skill '${skillName}'` };

  const runtime = readRuntime(runtimeId);
  if (!runtime) return { status: 'skipped', reason: `unknown runtime '${runtimeId}'` };

  const compat = (skill.manifest && skill.manifest.compatibility && skill.manifest.compatibility[runtimeId]) || 'unknown';
  if (!COMPATIBLE_STATUSES.has(compat) && !opts.includeUnknown) {
    return { status: 'skipped', reason: `compatibility '${compat}' for ${runtimeId} — not built (pass --include-unknown to force)` };
  }
  if (compat === 'unsupported') {
    return { status: 'skipped', reason: `declared unsupported for ${runtimeId}` };
  }

  const adapter = ADAPTERS[runtime.installStrategy];
  if (!adapter) {
    return { status: 'skipped', reason: `no adapter implemented for installStrategy '${runtime.installStrategy}' (${runtimeId})` };
  }

  const outDir = path.join(DIST_ROOT, 'skills', skillName, runtimeId);
  fs.rmSync(outDir, { recursive: true, force: true });
  const { files } = adapter(skill, outDir, runtime);

  const manifest = {
    schemaVersion: 1,
    skill: skillName,
    runtime: runtimeId,
    compatibility: compat,
    sourceVersion: (skill.manifest && skill.manifest.version) || '0.0.0',
    generatedAt: new Date().toISOString(),
    files,
  };
  fs.writeFileSync(path.join(outDir, 'distribution.json'), JSON.stringify(manifest, null, 2) + '\n');

  return { status: 'built', path: outDir, manifest };
}

module.exports = { buildSkillForRuntime, COMPATIBLE_STATUSES };

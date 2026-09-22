#!/usr/bin/env node
// Builds a pack's per-runtime distributions: dist/packs/<pack-id>/<runtime>/
// Reads packs/<id>/pack.json, resolves each skill from skills/, builds each
// skill's distribution (via buildSkillForRuntime) for every runtime at least
// one of the pack's skills is compatible with, then assembles the pack-level
// output for that runtime. Never modifies skills/ or packs/.
const fs = require('fs');
const path = require('path');
const { DIST_ROOT, PACKS_ROOT, listRuntimes, findSkill, readPack } = require('./lib/skills');
const { buildSkillForRuntime } = require('./lib/distribute');
const { copyDir } = require('./lib/adapters');

function buildPack(packId, opts = {}) {
  const packDir = path.join(PACKS_ROOT, packId);
  const packJsonPath = path.join(packDir, 'pack.json');
  if (!fs.existsSync(packJsonPath)) {
    throw new Error(`No pack.json found at packs/${packId}/pack.json`);
  }
  const pack = readPack(packId);
  const skillNames = pack.skills || [];
  if (skillNames.length === 0) {
    console.log(`packs/${packId}: no skills listed yet — nothing to build.`);
    return [];
  }

  const missing = skillNames.filter((name) => !findSkill(name));
  if (missing.length) {
    throw new Error(`packs/${packId}/pack.json references missing skill(s): ${missing.join(', ')}`);
  }

  const results = [];
  for (const runtimeId of listRuntimes()) {
    const builtSkills = [];
    const skipped = [];
    for (const skillName of skillNames) {
      const result = buildSkillForRuntime(skillName, runtimeId, opts);
      if (result.status === 'built') {
        builtSkills.push({ name: skillName, dir: result.path });
      } else {
        skipped.push({ name: skillName, reason: result.reason });
      }
    }

    if (builtSkills.length === 0) {
      results.push({ runtime: runtimeId, status: 'skipped', skipped });
      continue;
    }

    const runtimeOutDir = path.join(DIST_ROOT, 'packs', packId, runtimeId);
    fs.rmSync(runtimeOutDir, { recursive: true, force: true });
    fs.mkdirSync(runtimeOutDir, { recursive: true });
    fs.copyFileSync(packJsonPath, path.join(runtimeOutDir, 'pack.json'));

    for (const { name, dir } of builtSkills) {
      copyDir(dir, path.join(runtimeOutDir, name));
    }

    fs.writeFileSync(
      path.join(runtimeOutDir, 'pack-distribution.json'),
      JSON.stringify(
        {
          schemaVersion: 1,
          pack: packId,
          runtime: runtimeId,
          version: pack.version || '0.0.0',
          generatedAt: new Date().toISOString(),
          skills: builtSkills.map((s) => s.name),
          skipped,
        },
        null,
        2
      ) + '\n'
    );

    console.log(`Built packs/${packId}/${runtimeId} (${builtSkills.length}/${skillNames.length} skill(s))`);
    results.push({ runtime: runtimeId, status: 'built', path: runtimeOutDir, skills: builtSkills.map((s) => s.name), skipped });
  }

  const anyBuilt = results.some((r) => r.status === 'built');
  if (!anyBuilt) {
    console.log(`packs/${packId}: no runtime had a compatible + implemented adapter for any of its skills — nothing built.`);
  }
  return results;
}

if (require.main === module) {
  const packId = process.argv[2];
  const includeUnknown = process.argv.includes('--include-unknown');
  if (!packId) {
    console.error('Usage: node scripts/build-pack.js <pack-id> [--include-unknown]');
    process.exit(2);
  }
  try {
    buildPack(packId, { includeUnknown });
  } catch (err) {
    console.error(err.message);
    process.exit(1);
  }
}

module.exports = { buildPack };

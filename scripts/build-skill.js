#!/usr/bin/env node
// Builds distributions of one skill for every runtime it's compatible with
// (native/supported/adapted), or for a single runtime if given.
// Usage: node scripts/build-skill.js <skill> [runtime] [--include-unknown]
const { listRuntimes, findSkill } = require('./lib/skills');
const { buildSkillForRuntime } = require('./lib/distribute');

function buildSkill(skillName, runtimeId, opts = {}) {
  const skill = findSkill(skillName);
  if (!skill) throw new Error(`Unknown skill '${skillName}'`);

  const runtimeIds = runtimeId ? [runtimeId] : listRuntimes();
  const results = [];
  for (const id of runtimeIds) {
    const result = buildSkillForRuntime(skillName, id, opts);
    results.push({ runtime: id, ...result });
    if (result.status === 'built') {
      console.log(`Built ${skillName} -> dist/skills/${skillName}/${id}/`);
    } else {
      console.log(`Skipped ${skillName} / ${id}: ${result.reason}`);
    }
  }
  return results;
}

if (require.main === module) {
  const args = process.argv.slice(2).filter((a) => !a.startsWith('--'));
  const includeUnknown = process.argv.includes('--include-unknown');
  const [skillName, runtimeId] = args;
  if (!skillName) {
    console.error('Usage: node scripts/build-skill.js <skill> [runtime] [--include-unknown]');
    process.exit(2);
  }
  try {
    buildSkill(skillName, runtimeId, { includeUnknown });
  } catch (err) {
    console.error(err.message);
    process.exit(1);
  }
}

module.exports = { buildSkill };

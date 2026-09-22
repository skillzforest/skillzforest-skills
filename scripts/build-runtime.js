#!/usr/bin/env node
// Builds every skill that's compatible with one runtime.
// Usage: node scripts/build-runtime.js <runtime> [--include-unknown]
const { listSkills, readRuntime } = require('./lib/skills');
const { buildSkillForRuntime } = require('./lib/distribute');

function buildRuntime(runtimeId, opts = {}) {
  const runtime = readRuntime(runtimeId);
  if (!runtime) throw new Error(`Unknown runtime '${runtimeId}' — expected runtimes/${runtimeId}/runtime.json`);

  const results = [];
  for (const skill of listSkills()) {
    const result = buildSkillForRuntime(skill.name, runtimeId, opts);
    results.push({ skill: skill.name, ...result });
    if (result.status === 'built') {
      console.log(`Built ${skill.name} -> dist/skills/${skill.name}/${runtimeId}/`);
    } else {
      console.log(`Skipped ${skill.name} / ${runtimeId}: ${result.reason}`);
    }
  }
  return results;
}

if (require.main === module) {
  const runtimeId = process.argv[2];
  const includeUnknown = process.argv.includes('--include-unknown');
  if (!runtimeId) {
    console.error('Usage: node scripts/build-runtime.js <runtime> [--include-unknown]');
    process.exit(2);
  }
  try {
    buildRuntime(runtimeId, { includeUnknown });
  } catch (err) {
    console.error(err.message);
    process.exit(1);
  }
}

module.exports = { buildRuntime };

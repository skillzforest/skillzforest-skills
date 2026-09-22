#!/usr/bin/env node
// Builds every runtime distribution for every skill, then every pack.
// Packs with an empty skills list are reported and skipped.
const { listRuntimes, listPacks } = require('./lib/skills');
const { buildRuntime } = require('./build-runtime');
const { buildPack } = require('./build-pack');

let hadError = false;

for (const runtimeId of listRuntimes()) {
  try {
    buildRuntime(runtimeId);
  } catch (err) {
    hadError = true;
    console.error(`runtimes/${runtimeId}: ${err.message}`);
  }
}

for (const packId of listPacks()) {
  try {
    buildPack(packId);
  } catch (err) {
    hadError = true;
    console.error(`packs/${packId}: ${err.message}`);
  }
}

process.exit(hadError ? 1 : 0);

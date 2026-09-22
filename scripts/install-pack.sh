#!/usr/bin/env bash
set -euo pipefail

# Installs a pack's already-built runtime distribution locally, for testing.
# Only makes sense for a filesystem-strategy runtime (e.g. claude-code) — a
# runtime whose adapter produces an upload artifact (e.g. claude-ai's .skill
# zips) is installed by hand through that runtime's own UI instead.
#
# Usage: ./scripts/install-pack.sh dist/packs/<pack>/<runtime> [target_skills_dir]
# Default target (.agents/skills) matches the Codex runtime convention.
DIST_DIR=${1:-}
TARGET_SKILLS_DIR=${2:-.agents/skills}

if [ -z "$DIST_DIR" ] || [ ! -f "$DIST_DIR/pack-distribution.json" ]; then
  echo "Usage: $0 dist/packs/<pack>/<runtime> [target_skills_dir]" >&2
  echo "(run 'npm run build:pack -- <pack>' first if dist/packs/<pack>/<runtime> doesn't exist yet)" >&2
  exit 1
fi

RUNTIME_ID=$(python3 -c "import json; print(json.load(open('$DIST_DIR/pack-distribution.json'))['runtime'])")
INSTALL_STRATEGY=$(python3 -c "import json; print(json.load(open('runtimes/$RUNTIME_ID/runtime.json'))['installStrategy'])")
if [ "$INSTALL_STRATEGY" != "filesystem" ]; then
  echo "Runtime '$RUNTIME_ID' uses installStrategy '$INSTALL_STRATEGY', not 'filesystem' — nothing to copy locally." >&2
  echo "See runtimes/$RUNTIME_ID/README.md for how that runtime is actually installed." >&2
  exit 1
fi

mkdir -p "$TARGET_SKILLS_DIR"

for d in "$DIST_DIR"/*/; do
  name=$(basename "$d")
  dest="$TARGET_SKILLS_DIR/$name"
  rm -rf "$dest"
  cp -R "$d" "$dest"
  echo "Installed $name -> $dest"
done

PACK_ID=$(python3 -c "import json; print(json.load(open('$DIST_DIR/pack.json'))['id'])")
echo "Pack '$PACK_ID' installed into $TARGET_SKILLS_DIR"

#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/build_plugin.sh [plugins/ai-factory-av]
PLUGIN_DIR_REL=${1:-plugins/ai-factory-av}
REPO_ROOT=$(git rev-parse --show-toplevel)
PLUGIN_DIR="$REPO_ROOT/$PLUGIN_DIR_REL"

if [ ! -f "$PLUGIN_DIR/plugin.json" ]; then
  echo "Missing plugin.json in $PLUGIN_DIR" >&2
  exit 1
fi

ID=$(python3 -c "import json,sys
print(json.load(open('$PLUGIN_DIR/plugin.json'))['id'])")
VERSION=$(python3 -c "import json,sys
print(json.load(open('$PLUGIN_DIR/plugin.json'))['version'])")
SKILLS=$(python3 -c "import json,sys
data=json.load(open('$PLUGIN_DIR/plugin.json'))
print(' '.join(data.get('skills',[])))")

DIST="$REPO_ROOT/dist"
mkdir -p "$DIST"
ZIP="$DIST/${ID}-${VERSION}.zip"
rm -f "$ZIP"

echo "Building plugin $ID version $VERSION -> $ZIP"

FILES="$PLUGIN_DIR/plugin.json"
for s in $SKILLS; do
  if [ -d "$REPO_ROOT/.agents/skills/$s" ]; then
    FILES="$FILES .agents/skills/$s"
  else
    echo "Warning: skill '$s' not found under .agents/skills/$s" >&2
  fi
done

pushd "$REPO_ROOT" >/dev/null
# Exclude large or generated folders
EXCLUDE_ARGS=(".agents/skills/*/node_modules/*" ".agents/skills/*/out/*" "dist/*")
zip -r "$ZIP" $FILES -x "${EXCLUDE_ARGS[@]}"
popd >/dev/null

echo "Created $ZIP"

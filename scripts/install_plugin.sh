#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/install_plugin.sh path/to/plugin.zip [target_plugins_dir]
ZIP_PATH=${1:-}
TARGET_PLUGINS_DIR=${2:-.agents/plugins}

if [ -z "$ZIP_PATH" ] || [ ! -f "$ZIP_PATH" ]; then
  echo "Usage: $0 path/to/plugin.zip [target_plugins_dir]" >&2
  exit 1
fi

mkdir -p "$TARGET_PLUGINS_DIR"
TMP_DIR=$(mktemp -d)
unzip -q "$ZIP_PATH" -d "$TMP_DIR"

if [ ! -f "$TMP_DIR/plugin.json" ]; then
  echo "plugin.json not found inside zip" >&2
  rm -rf "$TMP_DIR"
  exit 1
fi

ID=$(python3 -c "import json,sys
print(json.load(open('$TMP_DIR/plugin.json'))['id'])")
DEST="$TARGET_PLUGINS_DIR/$ID"
mkdir -p "$DEST"
mv "$TMP_DIR"/* "$DEST/"
rm -rf "$TMP_DIR"

echo "Installed plugin $ID to $DEST"

# create symlinks for skills (if any) into .agents/skills
mkdir -p .agents/skills
for d in "$DEST"/av-*; do
  if [ -d "$d" ]; then
    name=$(basename "$d")
    ln -sfn "$PWD/$d" ".agents/skills/$name"
    echo "Linked .agents/skills/$name -> $d"
  fi
done

echo "Installation complete."

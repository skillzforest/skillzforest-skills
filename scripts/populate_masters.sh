#!/usr/bin/env bash
# Populate masters/ folders for skills from templates/documents
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES="$ROOT_DIR/templates/documents"
SKILLS_DIR="$ROOT_DIR/.agents/skills"

MAPPINGS="av-cadrage-fonctionnel:Cadrage_fonctionnel_template_MASTER.docx
av-cadrage-plateforme:Cadrage_plateforme_template_MASTER.docx
av-compte-rendu-reunion:Compte_rendu_reunion_template_MASTER.docx
av-devis:Devis_Modulaire_MASTER.xlsx
av-devis-tma:Devis_Modulaire_TMA_MASTER.xlsx
av-presentation-client:Presentation_MASTER.pptx
av-parcours-miro:User story mapping - Template.jpg
av-schema-logique:architecture-logique.json
av-schema-physique:architecture_physique.json
"

echo "Using templates from: $TEMPLATES"

echo "$MAPPINGS" | while IFS=: read -r skill filename; do
  src="$TEMPLATES/$filename"
  dest_dir="$SKILLS_DIR/$skill/masters"
  mkdir -p "$dest_dir"
  if [ -f "$src" ]; then
    cp -n "$src" "$dest_dir/" && echo "Copied $filename -> $dest_dir/"
  else
    echo "Template not found for $skill: $src (skipping)"
  fi
done

echo "Populate complete. Review each .agents/skills/*/masters/ folder."

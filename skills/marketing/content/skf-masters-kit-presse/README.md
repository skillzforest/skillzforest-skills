# skf-masters-kit-presse

Skill qui relève la charte graphique d'un site web, puis crée deux **masters** réutilisables pour présenter un produit digital à la presse, aux blogueurs et aux influenceurs :

- une **présentation presse** 16:9 (Google Slides ou .pptx), 17 slides au plan standard d'un lancement, avec une consigne de remplissage dans les notes de chaque slide ;
- un **document** (Google Docs ou .docx) : communiqué de presse, fiche créateurs, questions-réponses.

Les masters portent les couleurs, polices et logos du site, et des champs `{{CHAMP}}` à remplir à chaque campagne. Aucun contenu produit n'y est inventé.

## Installation

```bash
cp -r skf-masters-kit-presse ~/.claude/skills/        # ou .claude/skills/ d'un projet
python3 -m pip install python-pptx python-docx lxml
# vérification visuelle : LibreOffice (soffice) et poppler (pdftoppm)
```

## Utilisation

```bash
/skf-masters-kit-presse https://exemple.com
/skf-masters-kit-presse https://exemple.com --slides pptx --document docx --langue en
```

Étapes : relevé de la charte (charte publiée, puis styles calculés, puis CSS) → `brand-profile.json` → validation des contrastes et palettes (`scripts/brand_check.py`) → construction (`scripts/build_masters.py`) → conversion Google et insertion des logos par URL si demandé → vérification visuelle.

Scripts utilisables seuls :

```bash
python3 scripts/brand_check.py brand-profile.json
python3 scripts/build_masters.py brand-profile.json --out masters --logo logo.png --logo-clair logo-clair.png
```

## Contenu

```text
skf-masters-kit-presse/
├── SKILL.md
├── skill.json
├── scripts/
│   ├── brand_check.py        # contrastes WCAG, palettes slides et fond clair
│   └── build_masters.py      # .pptx et .docx depuis la charte et les plans
├── references/
│   ├── plan-slides.fr.json   # plan de la présentation (modifiable, traduisible)
│   └── plan-document.fr.json # plan du communiqué, de la fiche créateurs et des Q&R
└── examples/
    └── brand-profile.example.json
```

Pour une autre langue, traduire les deux plans en gardant les noms de champs, les clés et les types de blocs.

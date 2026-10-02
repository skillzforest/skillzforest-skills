# skf-design-extractor

Skill Claude Code qui extrait les vrais assets graphiques d'une ou plusieurs maquettes statiques (JPG, PNG) et les exporte en WebP, prêts à être intégrés dans une application web.

Elle découpe uniquement ce qui doit rester une image (photos, illustrations, logos, avatars, backgrounds, textures, captures, icônes spécifiques) et laisse de côté tout ce qui se reconstruit en HTML/CSS/React. Les pixels d'origine sont conservés : crop exact, réduction seulement, aucune IA générative.

Avec un **cahier de tailles** (Markdown, Excel ou CSV), chaque image est rattachée à sa ligne du cahier, exportée au ratio, à la taille et au poids demandés, et un rapport relie toutes les maquettes : ce qui est produit, ce qui manque, ce qu'il faut demander au designer.

## Installation

```bash
# Skill de projet (partagée via le dépôt)
cp -r skf-design-extractor .claude/skills/

# ou skill personnelle (tous les projets)
cp -r skf-design-extractor ~/.claude/skills/

python3 -m pip install Pillow openpyxl   # openpyxl seulement pour les cahiers .xlsx
```

## Utilisation

Une maquette, sans cahier :

```bash
/skf-design-extractor design/dashboard.jpg --dry-run
/skf-design-extractor design/dashboard.jpg
```

Plusieurs maquettes avec un cahier de tailles :

```bash
/skf-design-extractor design/home.png design/categorie.png --spec docs/assets-site.md --dry-run
/skf-design-extractor design/ --spec docs/assets-site.xlsx
```

Le `--dry-run` analyse, écrit les manifests et le rapport, sans créer d'image : c'est le moment de relire. La commande sans `--dry-run` repart des manifests existants et exporte.

Options :

```bash
--output public/assets/marketing     # dossier de sortie (racine si plusieurs maquettes ou --spec)
--padding 8                          # marge par défaut autour des crops
--min-confidence 0.7                 # seuil d'extraction automatique (défaut 0.80)
--allow-upscale                      # agrandit les crops trop petits (placeholder, signalé)
```

Résultat type avec cahier :

```text
public/assets/
├── assets-spec.json        # cahier normalisé
├── assets-map.json         # liens cahier <-> maquettes <-> fichiers
├── assets-report.md        # rapport de couverture
├── home/
│   ├── assets.json
│   ├── home-hero.webp
│   ├── skill-crm.webp
│   └── skill-crm-400x400.webp
└── categorie/
    ├── assets.json
    └── grand-theme-marketing.webp
```

Le dossier `public/` est servi tel quel par la plupart des frameworks : si les manifests et le rapport ne doivent pas être publics, utiliser `--output` vers un autre dossier puis copier les `.webp`.

## Le cahier de tailles

Format libre tant qu'il contient des tableaux avec au minimum une colonne **Emplacement** et une colonne **Taille à produire** (ou **Format**). Colonnes reconnues, quel que soit l'ordre :

| Colonne | Mots reconnus | Usage |
|---|---|---|
| Numéro | `#`, `N°`, `Ligne`, `Ref` | identifiant de ligne (`spec_id`) ; numérotation automatique sinon |
| Emplacement | `Emplacement`, `Usage`, `Élément` | `Page : composant` ; la page sert à repérer les manques par maquette |
| Largeur affichée | `Largeur affichée` | information |
| Format | `Format`, `Ratio` | ratio affiché (ex. `16:10`) |
| Taille | `Taille à produire`, `Résolution`, `Dimension` | `640 × 640` : taille et ratio de l'export |
| Poids | `Poids visé` | `≤ 60 Ko`, `≤ 2 Mo` : budget de l'export |
| Remarques | `Remarques`, `Notes` | notes attachées à la ligne |

Le reste est interprété aussi :

- **lignes de section** (une seule cellule remplie, ex. `**Catégories**`) ;
- **tableau sous un titre « Vidéos »** ou avec une colonne Durée : lignes vidéo, jamais produites depuis une maquette ;
- **« même image que la ligne 3 »** dans la taille : alias, rien à produire ;
- **« Même image, version mobile »** avec une taille : variante produite automatiquement avec la ligne précédente ;
- **règles communes** dans le texte : `qualité 75–80`, `1 Mo par image`, `pas de texte dans les images`, `10 % de marge` ;
- **précisions** `- **Ligne 5 :** ...` ou `- **Lignes 1 et 2 :** ...` : notes rattachées aux lignes.

En Excel, chaque feuille est lue comme une table (feuille « Vidéos » pour les vidéos) et une feuille de texte libre peut porter les règles. Exemples fournis : `examples/assets-site.example.md` et `examples/assets-site.example.xlsx` (mêmes données).

Une ligne du cahier décrit un **format**, pas une image : la ligne « Carte produit » couvre toutes les cartes produit trouvées dans les maquettes.

## Ce que fait l'export avec cahier

| Situation | Comportement |
|---|---|
| Ratio du cadre différent de la ligne | recadrage à l'intérieur du cadre visible, centré sur `focus` ; perte signalée au-delà de 2 % |
| Maquette qui n'affiche qu'une partie du visuel (carte 16:10 d'une image carrée) | export du carré disponible et demande de la source complète |
| Maquette plus petite que la taille demandée | export à la taille disponible, alerte « résolution insuffisante » (agrandissement seulement avec `--allow-upscale`) |
| Poids au-dessus du budget | qualité abaissée par paliers jusqu'à 60, puis alerte si le budget n'est toujours pas tenu |
| Variante déclarée (ex. version mobile) | fichier supplémentaire `<nom>-<L>x<H>.webp` |
| Même image sur plusieurs maquettes | détectée par empreinte perceptuelle ; une seule source extraite, les autres marquées `duplicate_of` |
| Texte posé sur la photo, visuel masqué ou coupé | non extrait, listé « à fournir par le designer » |
| Asset hors cahier (logo...) | export brut, listé « hors cahier » |

Astuce : exporter les maquettes en @2x depuis Figma. Le cahier vise en général du ×2 Retina ; une maquette en @1x déclenchera des alertes de résolution sur presque toutes les lignes.

## Le manifest `assets.json`

Un par maquette. Exemples : `examples/assets.example.json` (sans cahier) et `examples/assets.home-avec-cahier.example.json`.

| Champ | Requis | Description |
|---|---|---|
| `name` | oui | kebab-case, descriptif, unique dans la maquette |
| `type` | oui | `photo`, `illustration`, `logo`, `background`, `texture`, `decorative`, `screenshot`, `avatar`, `icon` |
| `x`, `y`, `width`, `height` | oui | zone visible de l'image dans la maquette (px source) |
| `confidence` | oui | 0 à 1 |
| `requires_reconstruction` | oui | `true` si les pixels de l'asset ne sont pas entièrement disponibles |
| `spec_id` | non | numéro de ligne du cahier |
| `output` | non | fichier principal (défaut `<name>.webp`) |
| `focus` | non | `[x, y]` entre 0 et 1 : point gardé lors du recadrage au ratio |
| `spec_variants` | non | limiter les lignes produites, ex. `[5]` |
| `duplicate_of` | non | `<maquette>/<asset>` : même image déjà extraite ailleurs |
| `padding` | non | marge ajoutée au cadre (défaut 0) |
| `reason`, `reconstruction_reason` | non | justifications affichées dans les rapports |
| `quality`, `lossless` | non | réglages WebP (hors cahier ; avec cahier, `quality` fixe le haut de la plage) |

Champs racine : `source`, `source_path` et `spec` (relatifs au manifest), `mockup`, `page` (libellé de page du cahier), `width`, `height`, `defaults` (`padding`, `min_confidence`, `allow_upscale`).

## Le script seul

`scripts/extract_design_assets.py` fonctionne sans Claude, par exemple après une retouche manuelle des manifests ou en CI :

```bash
S=.claude/skills/skf-design-extractor/scripts/extract_design_assets.py

python3 $S spec docs/assets-site.md --out public/assets/assets-spec.json   # lit le cahier
python3 $S info design/home.png                                            # dimensions, nom suggéré
python3 $S grid design/home.png                                            # grille de coordonnées
python3 $S zoom design/home.png --x 160 --y 2100 --width 664 --height 415
python3 $S snap design/home.png --x 80 --y 60 --width 300 --height 80
python3 $S preview --manifest public/assets/home/assets.json
python3 $S extract --manifest public/assets/home/assets.json --dry-run
python3 $S extract --manifest public/assets/home/assets.json [--json] [--allow-upscale] [--quality-floor 60]
python3 $S link public/assets                                              # rapport multi-maquettes
```

Les images de contrôle (`grid`, `zoom`, `preview`) vont dans le dossier temporaire du système.

Codes de sortie : `0` succès, `1` au moins un asset en erreur, `2` erreur bloquante (fichier introuvable, JSON invalide, dimensions incohérentes).

## Limites

- Les coordonnées et le rattachement aux lignes du cahier viennent de l'analyse visuelle de Claude : relire le `--dry-run`, la preview et le rapport.
- Le parsing du cahier est tolérant mais pas devin : une précision rédigée librement (« fournir l'image du bandeau en attendant un second champ ») doit être traduite à la main dans `assets-spec.json`. Claude le fait à l'étape 2 et le signale.
- Une maquette JPG n'a pas de transparence : un logo sur fond coloré sort avec son fond. Pour un logo détouré, utiliser le fichier source.
- La détection de doublons compare des cadres : la même image affichée à deux ratios différents n'est pas toujours repérée.

## Structure

```text
skf-design-extractor/
├── SKILL.md                                  # workflow de la skill
├── README.md                                 # cette documentation
├── scripts/
│   ├── extract_design_assets.py              # info, grid, zoom, snap, preview, extract, spec, link
│   └── asset_spec.py                         # lecture des cahiers md / xlsx / csv
└── examples/
    ├── assets-site.example.md                # cahier de tailles (Markdown)
    ├── assets-site.example.xlsx              # même cahier (Excel)
    ├── assets.example.json                   # manifest sans cahier
    ├── assets.home-avec-cahier.example.json  # manifest rattaché au cahier
    └── dashboard.png                         # maquette de démonstration
```

Essai rapide avec l'exemple sans cahier :

```bash
cd .claude/skills/skf-design-extractor
python3 scripts/extract_design_assets.py extract --manifest examples/assets.example.json --output /tmp/demo
python3 scripts/extract_design_assets.py spec examples/assets-site.example.xlsx
```

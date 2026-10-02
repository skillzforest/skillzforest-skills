---
name: skf-design-extractor
description: Extrait les vrais assets graphiques (photos, illustrations, logos, avatars, backgrounds, textures, captures, icônes spécifiques) d'une ou plusieurs maquettes statiques JPG ou PNG, avec ou sans cahier de tailles (Markdown, Excel ou CSV). Avec un cahier, rattache chaque image à sa ligne, l'exporte au ratio, à la taille et au poids demandés, et produit un rapport de couverture reliant toutes les maquettes. À utiliser dès que l'utilisateur veut extraire, découper ou préparer les images d'une maquette pour une application web, ou lance /skf-design-extractor.
argument-hint: <maquette.jpg|png|dossier>... [--spec <cahier.md|xlsx|csv>] [--dry-run] [--output <dossier>] [--padding <px>] [--min-confidence <0-1>] [--allow-upscale]
allowed-tools: Read, Write, Edit, Bash(python3:*), Bash(python:*), Bash(ls:*), Bash(mkdir:*)
---

# skf-design-extractor

Transforme une ou plusieurs maquettes statiques en assets réutilisables dans une application web.
Principe directeur : **conserver les pixels d'origine**. Crop exact, redimensionnement vers le bas seulement, aucune IA générative, aucune retouche, aucun pixel inventé.

Arguments reçus : `$ARGUMENTS`

Le script de référence est `scripts/extract_design_assets.py` dans le dossier de cette skill (noté `$S` ci-dessous ; utiliser le chemin réel). Il s'appuie sur `scripts/asset_spec.py` pour lire les cahiers. Toute la logique d'image passe par ce script, jamais par du code improvisé.

## 1. Lire les arguments

| Argument | Effet | Défaut |
|---|---|---|
| `<maquette>...` (obligatoire) | Un ou plusieurs JPG/PNG/WebP, ou un dossier (toutes ses images) | |
| `--spec <fichier>` | Cahier de tailles : `.md`, `.xlsx` ou `.csv` | aucun |
| `--dry-run` | Analyse, manifests et rapport, aucune image écrite | désactivé |
| `--output <dossier>` | Une maquette : dossier des assets. Plusieurs maquettes ou `--spec` : dossier racine | `public/assets/<maquette>/` ou `public/assets/` |
| `--padding <px>` | Marge par défaut autour des crops | `0` |
| `--min-confidence <0-1>` | Seuil d'extraction automatique | `0.80` |
| `--allow-upscale` | Agrandit les crops trop petits jusqu'à la taille du cahier (placeholder, signalé) | désactivé |

Organisation des fichiers :

```text
<racine>/                     # public/assets/ par défaut
├── assets-spec.json          # cahier normalisé (mode --spec)
├── assets-map.json           # liens cahier <-> maquettes <-> fichiers
├── assets-report.md          # rapport de couverture lisible
├── home/                     # un sous-dossier par maquette
│   ├── assets.json
│   └── *.webp
└── categorie/
```

Avec une seule maquette et sans `--spec`, le comportement reste celui d'origine : `public/assets/<maquette>/` et son `assets.json`.

Si une maquette ou le cahier est absent ou illisible, l'indiquer et s'arrêter.

## 2. Lire le cahier (si `--spec`)

```bash
python3 "$S" spec <cahier> --out <racine>/assets-spec.json
```

Le script reconnaît les tables (colonnes Emplacement, Format/Ratio, Taille à produire/Résolution, Poids visé, Remarques, colonne `#`), les sections, les règles communes (qualité, poids max, pas de texte, marge du sujet), les précisions « Ligne X : ... », les vidéos, et les liens entre lignes :

- `same_as` : la ligne réutilise le fichier d'une autre (« même image que la ligne 3 ») ; rien à produire.
- `variant_of` : la ligne est une autre taille de la même image (« Même image, version mobile ») ; produite automatiquement avec son parent.

Puis **relire le cahier d'origine et le JSON produit** et corriger `assets-spec.json` à la main si besoin. Une ligne du cahier décrit un format, pas une image unique : la ligne « Carte produit » couvre toutes les cartes produit. Points à vérifier :

- chaque ligne image a une `target` (largeur et hauteur à produire) ;
- les précisions qui changent le rattachement (par exemple « un seul champ image pour la carte et le bandeau : fournir le bandeau ») se traduisent en `same_as` ou `variant_of` ;
- le champ `page` (partie avant « : » de l'emplacement) est cohérent, il sert à vérifier qu'aucune image attendue ne manque dans une maquette.

Présenter à l'utilisateur un résumé court : lignes à produire, lignes alias, vidéos hors périmètre, corrections faites.

## 3. Mesurer et analyser chaque maquette

Pour chaque maquette :

```bash
python3 "$S" info <maquette>
python3 "$S" grid <maquette>
```

Lire la maquette (vue d'ensemble), puis la grille : les coordonnées se lisent toujours sur la grille, jamais sur une vue redimensionnée. Identifier la page représentée (nom du fichier, contenu) et la noter dans le manifest (`page`, libellé identique au cahier, ex. `Home`, `Page catégorie`).

### À extraire (fichier image)

`photo`, `illustration`, `logo`, `background` (fond graphique non reproductible en CSS), `texture`, `decorative`, `screenshot`, `avatar`, `icon` (seulement si spécifique au design et absente des librairies type Lucide, Heroicons, Material Symbols).

### À ne pas extraire (reconstruit en HTML/CSS/React)

Textes, boutons, inputs, formulaires, cards, containers, bordures, ombres, gradients simples, séparateurs, layouts, tableaux, navigation, composants UI standards, icônes génériques, graphiques de données.

## 4. Cadrer chaque asset

1. Repérer un cadre approximatif sur la grille.
2. Affiner : `python3 "$S" zoom <maquette> --x X --y Y --width W --height H` puis lire l'image (cadre vert = cadre testé).
3. Sur fond uni (logo, icône, avatar détouré) : `python3 "$S" snap <maquette> --x X --y Y --width W --height H`, à confirmer par un zoom.

Le cadre (`x`, `y`, `width`, `height`) décrit **la zone de l'image réellement visible** dans la maquette, sans le texte ni l'UI autour. Avec un cahier, ne jamais élargir le cadre pour atteindre le ratio demandé : le script recadre lui-même à l'intérieur du cadre et signale ce qui est perdu.

## 5. Rattacher au cahier (si `--spec`)

Pour chaque asset, renseigner `spec_id` = numéro de la ligne du cahier qui décrit cet emplacement. Indices : page de la maquette, composant (carte, bandeau, hero), taille affichée, ratio visible.

- Pointer la ligne principale ; ses variantes (`variant_of`) sont produites automatiquement (`<name>-<L>x<H>.webp`). Pour n'en produire qu'une partie : `"spec_variants": [5]`.
- Une ligne `same_as` est acceptée et redirigée vers sa ligne de référence.
- Un vrai asset absent du cahier (logo, par exemple) garde `spec_id` absent : il est exporté brut et listé « hors cahier ».
- `focus` (`[x, y]` entre 0 et 1, défaut `[0.5, 0.5]`) déplace le recadrage vers le sujet si le ratio du cahier diffère du cadre visible.
- Les règles du cahier s'appliquent à l'analyse : avec « pas de texte dans les images », tout texte incrusté ou posé sur le visuel donne `requires_reconstruction: true`.

## 6. Évaluer confiance et reconstruction

**`confidence`** (0 à 1) : certitude que l'élément doit être une image, netteté de ses limites, et en mode cahier certitude du rattachement à la ligne.

| Valeur | Situation type |
|---|---|
| 0.90 à 1.00 | Visuel isolé, bords nets, ligne du cahier évidente |
| 0.80 à 0.89 | Asset évident mais bords flous, ou rattachement probable |
| 0.50 à 0.79 | Doute réel sur la nature, les limites ou la ligne du cahier |
| < 0.50 | Hypothèse faible, garder pour mémoire |

**`requires_reconstruction: true`** dès que les pixels propres ne sont pas tous disponibles : texte, badge ou bouton posé dessus, visuel masqué par un composant, coupé par le bord, fusionné avec l'UI. Renseigner `reconstruction_reason` ; ne jamais prétendre récupérer les pixels cachés. Le script n'extrait pas ces assets et les liste « à fournir par le designer ».

## 7. Nommer

Lowercase, kebab-case, descriptif, orienté métier : `home-hero`, `skill-crm`, `besoin-communication`, `logo-acme`. Jamais `image-01`. Pour une série issue d'une même ligne du cahier, nommer chaque image par son contenu métier (le produit, la catégorie) lu dans la maquette.

## 8. Écrire les manifests

Un `assets.json` par maquette, dans son dossier de sortie :

```json
{
  "source": "home.png",
  "source_path": "../../../design/home.png",
  "spec": "../assets-spec.json",
  "mockup": "home",
  "page": "Home",
  "width": 2880,
  "height": 3000,
  "defaults": { "padding": 0, "min_confidence": 0.8 },
  "assets": [
    {
      "name": "skill-crm",
      "type": "photo",
      "spec_id": 5,
      "x": 160, "y": 2100, "width": 664, "height": 415,
      "focus": [0.5, 0.5],
      "confidence": 0.9,
      "requires_reconstruction": false,
      "reason": "Visuel produit, ligne 5 du cahier (carte produit).",
      "output": "skill-crm.webp"
    }
  ]
}
```

`source_path` et `spec` sont relatifs au manifest. `width`/`height` = valeurs de `info`. Champs optionnels : `padding`, `quality`, `lossless` (hors cahier), `focus`, `spec_variants`, `duplicate_of`, `reconstruction_reason`. Exemples complets dans `examples/`. Toujours écrire les manifests, y compris en `--dry-run`.

## 9. Relier les maquettes

```bash
python3 "$S" link <racine> [--spec <racine>/assets-spec.json]
```

Produit `assets-map.json` et `assets-report.md` à la racine, et indique :

- pour chaque ligne du cahier : produite, prête, à fournir, non trouvée dans la maquette de sa page, absente des maquettes, alias, variante, vidéo ;
- les **doublons probables** entre maquettes (empreinte perceptuelle des cadres) : la même image vue sur deux pages. Garder la source la plus grande et la moins masquée, et marquer l'autre `"duplicate_of": "<maquette>/<asset>"` dans son manifest. Vérifier visuellement avant de marquer : deux images proches ne sont pas forcément identiques ;
- les assets hors cahier.

Relancer `link` après chaque correction des manifests.

## 10. Contrôler avant extraction

Pour chaque maquette :

```bash
python3 "$S" preview --manifest <dossier>/assets.json
python3 "$S" extract --manifest <dossier>/assets.json --dry-run [--padding N] [--min-confidence S] [--allow-upscale]
```

Lire la preview (vert = à extraire, orange = confiance insuffisante, rouge = reconstruction, bleu = doublon, trait blanc fin = recadrage au ratio du cahier). Corriger les cadres si besoin.

Afficher ensuite à l'utilisateur, **avant toute extraction** :

| Maquette | Nom | Type | Ligne | Cadre | Coordonnées | Sortie(s) | Confiance | Statut | Justification |
|---|---|---|---|---|---|---|---|---|---|

Puis, en listes courtes : lignes du cahier non couvertes, assets à fournir par le designer, alertes de résolution (maquette trop petite pour la taille demandée), recadrages qui perdent une part du visuel, doublons retenus.

## 11. Extraire (mode normal uniquement)

En `--dry-run`, s'arrêter après l'étape 10 en indiquant les manifests, le rapport et la commande pour extraire.

Sinon, pour chaque maquette :

```bash
python3 "$S" extract --manifest <dossier>/assets.json [--padding N] [--min-confidence S] [--allow-upscale]
```

Puis relancer `link` pour mettre à jour le rapport avec les fichiers réellement écrits. Lire une ou deux images produites pour vérifier le cadrage. Conclure par : fichiers créés, lignes du cahier couvertes et manquantes, ce qu'il faut demander au designer.

## Comportement de l'export avec cahier

- **Ratio** : plus grand cadre au ratio de la ligne contenu dans le cadre visible, centré sur `focus`. Perte au-delà de 2 % signalée ; si la maquette n'affiche qu'un recadrage du visuel (carte 16:10 d'une image carrée), le rapport le dit et demande la source complète.
- **Taille** : réduction en Lanczos jusqu'à la taille de la ligne. Si la maquette est trop petite, export à la taille disponible et alerte « résolution insuffisante » ; agrandissement seulement avec `--allow-upscale`, toujours signalé.
- **Poids** : qualité WebP prise dans la plage du cahier (75 à 80 par défaut), abaissée par paliers jusqu'à `--quality-floor` (60) pour tenir le poids visé et le plafond par image ; tout dépassement restant est signalé.

## Règles absolues

- Aucune IA générative, aucun inpainting, aucune retouche : crops et redimensionnements uniquement.
- Aucun asset `requires_reconstruction: true`, sous le seuil, ou marqué `duplicate_of` n'est extrait.
- Les vidéos du cahier ne sont jamais produites depuis une maquette ; leurs images d'attente ou de couverture relèvent de leurs propres lignes.
- Ne jamais écraser une maquette ni le cahier source ; les images de contrôle restent hors des dossiers de sortie.
- Sur relance, partir des manifests et de `assets-spec.json` existants et les mettre à jour plutôt que de tout réanalyser, sauf demande contraire.

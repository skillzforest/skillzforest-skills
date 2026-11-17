---
name: skf-shorts-studio
description: >-
  Produit une vidéo courte verticale (short YouTube, TikTok, Reel Instagram,
  vidéo X et Bluesky) et sa cover à partir du kit source de skf-shorts-sources —
  choisit l'angle et l'accroche qui arrêtent le défilement, écrit le script
  écran par écran (une idée par écran, un mot surligné, coupe toutes les 2
  secondes, preuve, appel à l'action), le fait valider, puis rend avec Remotion
  la vidéo 9:16 (et 4:5 pour le fil) aux couleurs, polices et logo de la
  marque, avec démo, captures, chiffres animés, musique, et les covers
  marketées (9:16, 4:5, 1:1, miniature 16:9) au titre court et percutant ;
  vérifie chaque fichier contre les limites de chaque réseau et regarde le
  résultat image par image. À utiliser dès que l'utilisateur veut produire,
  monter ou générer un short, un reel, un TikTok, une vidéo verticale de promo
  d'un SaaS ou d'une idée, une cover ou une miniature de vidéo, ou lance
  /skf-shorts-studio.
argument-hint: "shorts/<slug> [--angle A|B|C|D|E] [--formats 9x16,4x5] [--draft] [--project <projet Remotion>]"
allowed-tools: Read, Write, Edit, Glob, Bash(python3:*), Bash(npx:*), Bash(npm:*), Bash(ls:*), Bash(mkdir:*), Bash(cp:*)
---

# skf-shorts-studio

Deuxième skill de la **Shorts Factory** (`skf-shorts-sources` → **`skf-shorts-studio`** →
`skf-shorts-publish`). Elle transforme un kit validé en **une vidéo qui accroche** et **une
cover qui donne envie de cliquer**, rendues par code avec Remotion : même charte, même
qualité à chaque fois, modifiable en une ligne.

Arguments reçus : `$ARGUMENTS`

Dossier de cette skill noté `$K` (utiliser le chemin réel). À lire avant d'écrire :
- `$K/references/editorial.md` — accroches, structures, règles d'écriture et de cover ;
- `$K/references/storyboard-format.md` — le format de `storyboard.json` ;
- `$K/references/formats.json` — limites et covers par réseau.

## 1. Lire le kit

`shorts/<slug>/kit.json` (format : `skf-shorts-sources/references/kit-format.md`). Il doit
être en `status: "validated"` ; sinon, ou s'il manque, proposer `/skf-shorts-sources`.
Relire les faits, la douleur, l'action attendue, le ton ; **regarder** les captures et les
images du kit (lecture d'image) pour savoir ce qu'elles montrent vraiment.

Vidéos et sons sans durée dans le kit :

```bash
python3 "$K/scripts/render_short.py" shorts/<slug> --probe-assets
```

## 2. Choisir l'angle et l'accroche

D'après `editorial.md` : la structure (A problème → solution, B avant/après, C liste, D démo
express, E conviction) et la formule d'accroche qui collent aux sources (une démo forte, un
chiffre fort, plusieurs bénéfices, une idée). Proposer **3 accroches** différentes, chacune
avec le titre de cover qui va avec, et recommander la meilleure en une phrase.

## 3. Écrire le script

Écrire `shorts/<slug>/storyboard.json` (`status: "draft"`) :

- 15 à 35 s, 5 à 8 scènes ; une idée par écran, 7 mots au plus, un `highlight` par écran ;
- le produit visible avant 40 % de la durée, en vrai (capture, démo) ;
- chaque chiffre, fonctionnalité ou promesse vient de `kit.facts` (ids dans `factsUsed`) ;
- `brand` recopiée du kit, chemins sans le préfixe `assets/` ; `handle` = URL courte ou compte ;
- `formats` : `9x16`, plus `4x5` si X, Bluesky ou LinkedIn sont visés ;
- `music` seulement si sa licence est connue (`own`, `royalty-free`, `cc0`, `cc-by`) ;
- `cover` : titre de 2 à 5 mots = la promesse de l'accroche, un mot surligné, un badge
  si utile, le meilleur visuel du produit ;
- la langue et le tutoiement ou vouvoiement de `kit.brand.tone`.

Montrer le script **sous forme lisible** — un tableau scène / durée / texte à l'écran /
visuel — avec l'accroche, la cover, la musique et la durée totale, puis demander la
validation. Sur accord : `status: "approved"`. Une remarque : corriger et remontrer.

## 4. Rendre

```bash
python3 "$K/scripts/render_short.py" shorts/<slug> --draft     # aperçu rapide, demi-taille
python3 "$K/scripts/render_short.py" shorts/<slug>             # rendu final
```

- Premier usage : pas de projet Remotion → ajouter `--scaffold` (installe Remotion dans
  `~/.skf-shorts/remotion`, réseau requis, quelques minutes) ou `--project <projet>` pour
  utiliser un projet existant. Les templates sont copiés dans `src/skf-shorts-studio/` du
  projet ; son `Root` n'est jamais modifié — le dire à l'utilisateur.
- Sorties dans `shorts/<slug>/out/` : `short-9x16.mp4` (+ `short-4x5.mp4`), `cover-*.jpg`,
  `thumb-16x9.jpg`, `frames/` (image 0 et milieu de chaque scène), `sheet.jpg` (planche,
  si Pillow est installé), `render.json` (mesures et vérifications par réseau).
- `--only covers` pour refaire seulement les covers, `--only sheet` pour la planche.

## 5. Regarder, corriger

**Regarder** `sheet.jpg` (ou chaque image de `frames/`) et chaque cover avant de conclure :

- image 0 : l'accroche se lit-elle comme une cover ? (X, Bluesky, TikTok la prennent comme
  vignette) ;
- texte coupé, trop petit, mot isolé en fin de ligne, surlignage mal placé → raccourcir le
  texte ou changer `highlight` ;
- visuel illisible ou mal cadré → changer `frame`, `fit`, `zoom`, `trimBefore` ;
- cover : titre lisible en vignette (imaginer 200 px de large), visuel net, logo lisible ;
  le titre et le visuel restent-ils dans le carré central ?
- `render.json > checks` : chaque réseau `ok` ; `advice` : durée hors de la zone conseillée.

Corriger le storyboard et relancer jusqu'à un résultat propre (deux ou trois passes au plus,
puis montrer à l'utilisateur ce qui reste discutable). Passer `status` à `rendered`.

## 6. Rendre compte

- L'angle, l'accroche, la durée, les faits cités.
- Les fichiers (chemins absolus), leur poids, les vérifications par réseau.
- Ce qui reste à décider : musique ajoutée à l'envoi (aucune sous licence), logo en basse
  définition, faits à confirmer.
- Proposer `/skf-shorts-publish shorts/<slug>` pour les légendes et la publication.

## Règles

- Rien d'inventé : ni chiffre, ni fonctionnalité, ni témoignage, ni logo de client.
- La charte vient du kit ; ne pas modifier le kit depuis cette skill (le signaler et proposer
  `/skf-shorts-sources` pour le corriger).
- Ne jamais toucher au code du projet Remotion de l'utilisateur en dehors de
  `src/skf-shorts-studio/`.

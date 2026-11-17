# Format du storyboard — `shorts/<slug>/storyboard.json`

Le storyboard **est** la vidéo : `render_short.py` le passe tel quel aux templates Remotion
(`templates/remotion/schema.ts` fait foi). Les chemins de fichiers sont **relatifs à
`shorts/<slug>/assets/`** (dans `kit.json` ils sont relatifs au dossier du short : retirer le
préfixe `assets/`).

```json
{
  "status": "draft",
  "angle": "A — problème → solution",
  "hookFormula": "question douleur",
  "platforms": ["youtube", "tiktok", "instagram", "x", "bluesky"],
  "formats": ["9x16", "4x5"],
  "covers": ["9x16", "16x9"],
  "factsUsed": ["f1", "f2"],

  "language": "fr",
  "brand": {
    "name": "Acme",
    "colors": { "bg": "#0E1525", "bg2": "#1D2B53", "text": "#FFFFFF", "muted": "#B8C1DA", "accent": "#FFD23F", "accentText": "#0E1525" },
    "fonts": { "display": "'Plus Jakarta Sans', sans-serif", "body": "Inter, sans-serif" },
    "fontFiles": [{ "family": "Plus Jakarta Sans", "file": "fonts/PlusJakartaSans-400-800.woff2", "weight": "400 800" }],
    "logo": "site/logo-1.svg",
    "handle": "acme.app",
    "pattern": "grid"
  },
  "scenes": [
    { "type": "hook", "duration": 2, "text": "Tes devis te prennent 3 heures ?", "highlight": "3 heures", "emoji": "😩" },
    { "type": "statement", "duration": 2.5, "text": "Copier, coller, recalculer… à la main", "strike": "à la main" },
    { "type": "reveal", "duration": 2, "tagline": "Acme écrit le devis à ta place" },
    { "type": "media", "duration": 5, "caption": "Tu décris. Il chiffre.", "highlight": "Il chiffre.",
      "media": { "file": "media/demo.mp4", "kind": "video", "frame": "none", "aspect": 1.7778, "trimBefore": 3 } },
    { "type": "media", "duration": 3.5, "caption": "Prêt à envoyer", "highlight": "envoyer",
      "media": { "file": "site/screens/home-mobile.png", "kind": "image", "frame": "phone" } },
    { "type": "stat", "duration": 2.5, "value": 4800, "label": "artisans ne font plus leurs devis le soir" },
    { "type": "cta", "duration": 3, "text": "Essaie-le sur ton prochain devis", "button": "acme.app" }
  ],
  "music": { "file": "media/upbeat.mp3", "volume": 0.5, "trimBefore": 0 },
  "progressBar": true,
  "cover": {
    "title": "Tes devis en 30 secondes",
    "highlight": "30 secondes",
    "badge": "Démo",
    "visual": { "file": "site/screens/home-mobile.png", "kind": "image", "frame": "phone" }
  }
}
```

## En-tête (non rendu)

| Champ | Contenu |
|---|---|
| `status` | `draft` → `approved` quand l'utilisateur valide le script, `rendered` après le rendu final |
| `angle`, `hookFormula` | structure et formule d'accroche choisies (`editorial.md`) |
| `platforms` | repris du kit |
| `formats` | vidéos à rendre : `9x16` (toujours), `4x5` (X, Bluesky, LinkedIn sur ordinateur), `1x1` |
| `covers` | covers à rendre : `9x16`, `4x5`, `1x1`, `16x9` ; absent = ce que demandent les plateformes (`formats.json`) |
| `factsUsed` | ids des faits du kit cités à l'écran |

## Scènes

Toutes ont `duration` (secondes, 0,6 à 15). 2 à 12 scènes.

| `type` | Champs | À l'écran |
|---|---|---|
| `hook` | `text`, `highlight?`, `emoji?`, `media?` (fond assombri) | accroche lisible **dès l'image 0** (vignette automatique), légère respiration |
| `statement` | `text`, `highlight?`, `strike?`, `emoji?` | mots qui apparaissent un à un, `strike` rayé à mi-scène |
| `media` | `media`, `caption?`, `highlight?` | légende en haut, visuel qui entre en glissant, zoom lent |
| `list` | `items` (2–4), `title?`, `marker` (`check`, `number`, `cross`) | cartes qui arrivent une à une |
| `stat` | `value`, `label`, `prefix?`, `suffix?`, `decimals?` | compteur qui monte jusqu'à la valeur |
| `reveal` | `tagline` | logo qui surgit avec une onde, phrase de marque |
| `cta` | `text`, `button`, `url?` | appel à l'action, bouton qui pulse, logo |

`media` : `file`, `kind` (`image` ou `video`), `frame` (`phone`, `browser`, `none`, `full`), `zoom`
(`in`, `out`, `none`), `fit` (`cover`, `contain`), `aspect` (largeur / hauteur du fichier, à
reprendre du kit), `trimBefore` (secondes sautées au début d'une vidéo), `focusX` / `focusY`
(0 à 1, 0,5 par défaut : la partie du fichier gardée quand il est recadré).

- Capture mobile → `frame: "phone"` ; capture desktop → `frame: "browser"` ; vidéo paysage
  → `frame: "none"` avec `aspect` : elle passe en pleine largeur sur un fond flou d'elle-même.
- Images de jeu, de vol, de film → `frame: "full"` : le plan occupe tout l'écran, recadré dans le
  fichier (une capture 16:9 devient un plan 9:16 : `focusX` place la fenêtre sur le sujet), la
  légende passe en haut sur un voile. Dans un `hook`, le plan reste lumineux sous le texte. Un
  plan 16:9 dont le sens tient à toute sa largeur (un titre incrusté) reste en `frame: "none"`.
- Les vidéos sont muettes dans le short : le son vient de `music` (et `voice`).
- Une vidéo source doit couvrir toute sa scène : `trimBefore + duration` ≤ durée du fichier
  (dans le kit), sinon la fin de la scène se fige ou se vide.

## Son

- `music` : `file`, `volume` (0,55 par défaut), `trimBefore` (démarrer sur le moment fort) ;
  fondu d'entrée et de sortie automatiques.
- `voice` (facultatif) : une voix off enregistrée (`file`, `volume`) ; la musique baisse
  alors d'elle-même.
- `sounds` (facultatif) : bruitages et morceaux posés sur la ligne de temps, `[{ file, at, volume,
  trimBefore, duration }]` (`at` en secondes depuis le début du short) : une explosion calée sur
  l'impact, une ambiance sous quelques scènes, ou une musique montée en deux morceaux (le corps,
  puis le coup final du morceau sur l'appel à l'action) à la place de `music`.

## Texte

Une espace insécable (U+00A0) garde des mots sur la même ligne (« 6 juin 1944 ») ; un
`highlight` d'un ou deux mots laisse le texte plus grand qu'une phrase entière surlignée, qui doit
tenir sur une ligne.

## Cover

`title` (2 à 5 mots), `highlight` (mots du titre sur le bloc d'accent), `kicker` (petite ligne
au-dessus), `badge` (1–2 mots), `visual` (même objet que `media` ; `frame: "full"` en fait le fond
entier de la cover, sous un voile : une image de jeu ou de film).

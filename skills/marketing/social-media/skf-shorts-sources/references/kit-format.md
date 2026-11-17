# Format du kit source — `shorts/<slug>/kit.json`

Le kit est **l'unique entrée** de `skf-shorts-studio` (production) et de `skf-shorts-publish`
(diffusion). Tout chemin de fichier est **relatif au dossier du short**.

```text
shorts/<slug>/
├── kit.json            # ce fichier
├── assets/             # tout ce qui peut apparaître à l'écran ou s'entendre
│   ├── site/           # og-image, logos, icônes, screens/ (captures desktop et mobile)
│   ├── media/          # images, vidéos, sons apportés par l'utilisateur
│   └── fonts/          # polices (woff2)
├── docs/               # documents sources (PDF, Word, PowerPoint…) — jamais rendus
└── inbox/              # bruts : site.json, textes extraits, téléchargements cloud
```

## Exemple

```json
{
  "version": 1,
  "slug": "acme-devis-30s",
  "createdAt": "2026-11-17",
  "status": "validated",
  "language": "fr",
  "platforms": ["youtube", "tiktok", "instagram", "x", "bluesky"],
  "idea": {
    "subject": "Acme écrit un devis complet en 30 secondes à partir d'une description",
    "goal": "inscriptions à l'essai",
    "audience": "artisans et indépendants qui font leurs devis le soir",
    "pain": "3 heures par semaine perdues à copier-coller des devis",
    "cta": { "text": "Essaie-le sur ton prochain devis", "url": "https://acme.app", "button": "acme.app" }
  },
  "product": {
    "name": "Acme",
    "url": "https://acme.app",
    "pitch": "Le devis écrit pour toi, prêt à envoyer.",
    "handle": "@acme_app"
  },
  "brand": {
    "name": "Acme",
    "colors": { "bg": "#0E1525", "bg2": "#1D2B53", "text": "#FFFFFF", "muted": "#B8C1DA", "accent": "#FFD23F", "accentText": "#0E1525" },
    "fonts": { "display": "'Plus Jakarta Sans', Inter, sans-serif", "body": "Inter, sans-serif" },
    "fontFiles": [
      { "family": "Plus Jakarta Sans", "file": "assets/fonts/PlusJakartaSans-400-800.woff2", "weight": "400 800" }
    ],
    "logo": "assets/site/logo-1.svg",
    "tone": "tutoiement, phrases courtes, concret, un brin d'humour",
    "origin": {
      "colors": "variables CSS --color-navy, --color-yellow de acme.app",
      "fonts": "Google Fonts chargée par acme.app",
      "logo": "logo de l'en-tête de acme.app"
    },
    "toCheck": ["bg2 dérivée : #1D2B53 est la couleur des cartes, pas un fond déclaré"]
  },
  "facts": [
    { "id": "f1", "text": "Un devis complet en 30 secondes", "source": "https://acme.app (titre h1)", "kind": "feature" },
    { "id": "f2", "text": "4 800 artisans l'utilisent", "source": "docs/plaquette.pdf p. 2", "kind": "number" }
  ],
  "assets": [
    { "id": "a1", "kind": "image", "file": "assets/site/screens/home-mobile.png", "origin": "site", "source": "https://acme.app", "width": 780, "height": 1688, "licence": "own" },
    { "id": "a2", "kind": "video", "file": "assets/media/demo.mp4", "origin": "gdrive", "source": "Drive : Marketing/Démo/demo.mp4", "width": 1080, "height": 1920, "duration": 41.2, "licence": "own" },
    { "id": "a3", "kind": "audio", "file": "assets/media/upbeat.mp3", "origin": "local", "source": "~/Music/upbeat.mp3", "duration": 92.0, "licence": "royalty-free", "note": "Pixabay, licence de contenu" }
  ],
  "notes": "Éviter de citer le concurrent X. Prix non communiqué publiquement."
}
```

## Champs

| Champ | Requis | Contenu |
|---|---|---|
| `status` | oui | `draft` pendant la collecte, `validated` quand l'utilisateur a validé le récapitulatif |
| `language` | oui | langue de la vidéo et des textes (`fr`, `en`…) |
| `platforms` | oui | parmi `youtube`, `tiktok`, `instagram`, `x`, `bluesky` (et `linkedin`, `threads`, `facebook`) |
| `idea.subject` | oui | l'idée à illustrer, en une phrase, avec le bénéfice |
| `idea.goal` | non | ce que la vidéo doit déclencher (inscriptions, visites, notoriété, lancement) |
| `idea.audience`, `idea.pain` | conseillé | pour qui, et la douleur concrète qu'on nomme dans l'accroche |
| `idea.cta` | conseillé | `text` (phrase de fin), `url`, `button` (texte court du bouton) |
| `product` | oui | `name`, `url`, `pitch` (1 phrase), `handle` |
| `brand.colors` | oui | 6 couleurs `#RRGGBB` : `bg`, `bg2` (2e teinte du dégradé), `text`, `muted`, `accent`, `accentText` (texte posé sur l'accent) |
| `brand.fonts` | oui | `display` (titres) et `body`, en familles CSS avec repli |
| `brand.fontFiles` | conseillé | fichiers sous `assets/fonts/` (`fetch_font.py`) ; sans eux, polices système |
| `brand.logo` | conseillé | fichier sous `assets/`, **lisible sur `bg`** (version claire sur fond sombre) |
| `brand.tone` | conseillé | tutoiement ou vouvoiement, longueur des phrases, registre |
| `brand.origin` | oui si relevé | d'où vient chaque valeur (site, charte PDF, demande de l'utilisateur) |
| `brand.toCheck` | non | valeurs déduites ou approchées, à confirmer |
| `facts[]` | oui (≥ 3 conseillé) | affirmations utilisables à l'écran, **chacune avec sa source** (URL, fichier + page) |
| `assets[]` | oui | écrit par `collect_media.py` ; `licence` : `own`, `cc0`, `cc-by` (+ crédit dans `note`), `royalty-free`, `unknown` |

## Règles

- **Rien d'inventé** : une couleur, un chiffre, une fonctionnalité, un prix absents des sources
  n'entrent pas dans le kit. Une couleur manquante se déduit d'une couleur relevée
  (assombrie, éclaircie) et se note dans `toCheck`.
- Contraste exigé par `validate_kit.py` : `text`/`bg`, `text`/`bg2` et `accentText`/`accent`
  ≥ 4,5:1 — un short se lit sur un téléphone, en plein soleil, en 2 secondes.
- Musique et vidéos de tiers : licence connue, sinon on ne les publie pas (TikTok et
  Instagram coupent le son ou bloquent la vidéo).

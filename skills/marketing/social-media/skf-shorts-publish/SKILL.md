---
name: skf-shorts-publish
description: >-
  Diffuse un short produit par skf-shorts-studio sur YouTube Shorts, TikTok,
  Instagram Reels, X et Bluesky (et LinkedIn, Threads, Facebook) — écrit une
  légende propre à chaque réseau (titre YouTube, accroche, hashtags, lien, texte
  alternatif), choisit pour chacun la bonne vidéo (9:16 ou 4:5) et la bonne
  cover, fait tout valider, puis publie, programme ou met en brouillon en une
  fois par l'API de Postiz (auto-hébergé ou Postiz Cloud), ou prépare un kit
  d'envoi à la main avec les fichiers et les textes prêts à coller ; journal
  des envois et suivi des liens publiés. À utiliser dès que l'utilisateur veut
  publier, programmer, poster ou partager une vidéo courte, un short, un reel
  ou un TikTok sur les réseaux sociaux, écrire les légendes d'une vidéo, ou
  lance /skf-shorts-publish.
argument-hint: "shorts/<slug> [--kit] [--when now|schedule|draft] [--date ISO] [--only youtube,tiktok] [--status]"
allowed-tools: Read, Write, Edit, Glob, Bash(python3:*), Bash(ls:*), Bash(open:*)
---

# skf-shorts-publish

Dernière skill de la **Shorts Factory** (`skf-shorts-sources` → `skf-shorts-studio` →
**`skf-shorts-publish`**). Elle ne publie **rien sans accord explicite** de l'utilisateur.

Arguments reçus : `$ARGUMENTS`

Dossier de cette skill noté `$K` ; tout passe par `$K/scripts/publish.py` (Python 3,
bibliothèque standard). Format et règles d'écriture : `$K/references/publish-format.md`.

## 1. Vérifier ce qu'on publie

- `shorts/<slug>/out/render.json` : chaque réseau visé doit être `ok` dans `checks`, et le
  rendu ne doit pas être un brouillon (`draft: false`). Sinon renvoyer vers
  `/skf-shorts-studio`.
- **Regarder** la cover et `out/sheet.jpg` (ou `out/frames/`) une dernière fois.
- Licences : une musique ou une vidéo `unknown` dans `kit.json` → ne pas publier, le dire.

## 2. Écrire les légendes

Écrire `shorts/<slug>/publish.json` (`status: "draft"`), une cible par réseau du kit :

- vidéo : `out/short-4x5.mp4` pour X, Bluesky, LinkedIn quand elle existe, sinon
  `out/short-9x16.mp4` ; cover : `out/cover-9x16.jpg` (Instagram, Facebook),
  `out/thumb-16x9.jpg` (YouTube), `out/cover-4x5.jpg` (LinkedIn) ;
- texte réécrit pour chaque réseau d'après `publish-format.md` : il prolonge l'accroche de
  la vidéo, reprend les mêmes faits, dit quoi faire ; titre YouTube avec le mot que le
  public cherche ; texte alternatif pour Bluesky ;
- quand publier : demander (maintenant, à une date, brouillon) ; proposer d'étaler les
  réseaux sur quelques jours.

```bash
python3 "$K/scripts/publish.py" validate shorts/<slug>
```

Corriger jusqu'à `ok: true`. Montrer un **récapitulatif** par réseau : compte, vidéo, cover,
titre, texte complet avec hashtags, date. Sur **accord explicite**, passer `status` à
`approved`.

## 3a. Publier avec Postiz (recommandé)

Postiz publie sur tous ces réseaux par une seule API. Configuration : `POSTIZ_URL` (instance
auto-hébergée, ex. `http://127.0.0.1:4007`, ou `https://api.postiz.com` pour Postiz Cloud) et
`POSTIZ_API_KEY` (Postiz → Settings → Public API), dans l'environnement ou un `.env`. Ne
jamais afficher ni écrire la clé ailleurs.

```bash
python3 "$K/scripts/publish.py" check                       # connexion, nombre de canaux
python3 "$K/scripts/publish.py" bind shorts/<slug> --write  # relie chaque réseau à son canal Postiz
python3 "$K/scripts/publish.py" settings <integrationId>    # règles et réglages en direct d'un canal
```

- Un réseau sans canal connecté : le connecter dans Postiz (Add Channel), ou le passer en
  `skip`, ou le publier à la main (3b).
- `settings <id>` : si le canal accepte une miniature ou une couverture, la donner dans
  `targets[].settings` avec `"@upload:out/thumb-16x9.jpg"` ; remplir aussi les réglages
  obligatoires qu'il annonce (visibilité, confidentialité TikTok, divulgation de marque).
- Instagram et TikTok vont chercher la vidéo par URL : l'instance Postiz doit être joignable
  en HTTPS depuis Internet (serveur ou tunnel). Une instance seulement locale échouera sur ces
  deux réseaux — le dire avant d'envoyer.

Simuler, montrer, puis envoyer **sur accord** :

```bash
python3 "$K/scripts/publish.py" send shorts/<slug> --dry-run
python3 "$K/scripts/publish.py" send shorts/<slug>
```

Le script envoie les médias une fois (cache dans `publish-log.json`), crée les posts (une
requête par date), journalise et met à jour `status` (`published`, `scheduled`, `drafted`,
`partial`). Un réseau déjà envoyé est sauté (`--force` pour renvoyer, seulement sur demande) ;
`--only` limite l'envoi ; `--type` et `--date` remplacent `when`.

Pas de Postiz et l'utilisateur en veut un : self-hosting par Docker (documentation officielle
de Postiz) ou Postiz Cloud ; si la Social Factory SkillzForest est installée, réutiliser son
instance et son `.env`.

## 3b. Publier à la main (sans Postiz)

```bash
python3 "$K/scripts/publish.py" kit shorts/<slug>
```

Crée `shorts/<slug>/upload-kit/` : un dossier par réseau (vidéo, cover, `caption.txt`,
`title.txt`, `alt.txt`) et `UPLOAD.md` avec le lien d'envoi et les étapes de chaque
réseau (dont le choix de la couverture). Ouvrir le dossier pour l'utilisateur.

## 4. Suivre

```bash
python3 "$K/scripts/publish.py" status --from 2026-11-01T00:00:00Z
```

Rapporter réseau par réseau : publié (lien), programmé (date), brouillon, sauté (raison),
erreur (message de Postiz). Une erreur sur un réseau se relance depuis l'interface Postiz ou
avec `send --only <réseau> --force` après correction.

## Règles

- Jamais d'envoi sans `status: "approved"` posé sur accord explicite de l'utilisateur.
- Jamais d'appel direct aux API des réseaux, jamais d'identifiants de compte demandés :
  Postiz ou l'envoi à la main.
- Une publication ratée n'est pas renvoyée en boucle : une tentative, puis rapport.

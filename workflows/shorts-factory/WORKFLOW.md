# Workflow : Shorts Factory

## Objectif

Passer d'une idée (un SaaS, une fonctionnalité, une conviction) à un short publié sur YouTube Shorts, TikTok,
Instagram Reels, X et Bluesky, avec une cover marketée, aux couleurs de la marque, sans rien inventer.

## Étapes

| # | Skill | Entrée | Sortie | Validation humaine |
|---|---|---|---|---|
| 1 | `skf-shorts-sources` | réseaux, idée, action, sources (site, documents, cloud, vidéos, sons) | `shorts/<slug>/kit.json`, `assets/`, `docs/` | récapitulatif du kit (charte, faits, médias, licences) |
| 2 | `skf-shorts-studio` | `kit.json` validé | `storyboard.json`, `out/short-9x16.mp4` (+ 4:5), `out/cover-*.jpg`, `out/thumb-16x9.jpg`, `out/render.json` | script écran par écran, puis la vidéo et les covers |
| 3 | `skf-shorts-publish` | `out/render.json` sans erreur | `publish.json`, `publish-log.json` ou `upload-kit/` | légendes par réseau et date, avant tout envoi |

Chaque étape relit le fichier de la précédente : on peut s'arrêter, reprendre un autre jour, ou refaire une étape
seule (une autre accroche, une autre cover, une autre date) sans refaire les autres.

## Prérequis

- Python 3 ; Node.js 18+ et Remotion (installé une fois par `render_short.py --scaffold`) ; Chrome, Chromium ou
  Edge pour les captures du site ; Pillow facultatif (planche-contact).
- Pour publier automatiquement : une instance Postiz (auto-hébergée ou Postiz Cloud) avec les comptes connectés,
  `POSTIZ_URL` et `POSTIZ_API_KEY`. Sans Postiz : kit d'envoi à la main.

## Variantes

- **Série** : un kit, plusieurs storyboards (`shorts/<slug>-1`, `-2`…) en changeant d'angle — même charte, mêmes
  faits, accroches différentes ; publier à quelques jours d'écart.
- **Avec la Social Factory** : `skf-shorts-publish` réutilise l'instance Postiz et le `.env` de la Social Factory ;
  les annonces texte restent à `skf-social-compose`.
- **Avec la Growth Factory** : une opportunité approuvée dans `skf-campaign-studio` qui demande une vidéo courte
  devient l'idée de l'étape 1.

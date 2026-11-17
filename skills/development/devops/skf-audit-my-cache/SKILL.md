---
name: skf-audit-my-cache
description: >-
  Audit noté de la politique de cache HTTP d'un site web : une note sur 100,
  une lettre (A à E) et six indicateurs chiffrés avec leur statut (réutilisation
  à la deuxième visite, validateurs et 304, noms de fichiers versionnés, durées
  adaptées, compression, sécurité). Examine les pages HTML, scripts, styles,
  images, polices, réponses d'API et redirections telles qu'un visiteur
  anonyme les reçoit et qu'un visiteur connecté devrait les recevoir :
  fichiers versionnés ou non, durée de conservation, validateurs ETag et
  Last-Modified et réponses 304, compression, cookies sur des réponses
  partagées. Mesure ce qu'une deuxième visite retélécharge, retrouve dans le
  code ou la configuration du serveur (Caddy, nginx, Apache, Express, Next.js,
  Vercel, Netlify, Cloudflare) l'origine de chaque règle, puis propose une
  politique cible, anonyme et connecté, avec les correctifs prêts à appliquer.
  À utiliser dès que l'utilisateur demande un audit ou une note de cache, quel
  est le cache de son site, si
  son site se met bien en cache, pourquoi tout se recharge à chaque visite,
  pourquoi les visiteurs voient une ancienne version après une mise en ligne,
  veut améliorer le cache ou les en-têtes Cache-Control, ou lance
  /skf-audit-my-cache.
argument-hint: "[url du site] [--api /chemin,/chemin] [--pages 3]"
allowed-tools: Read, Grep, Glob, Bash(node:*), Bash(curl:*), Bash(ls:*), Bash(git:*)
---

# Audit my cache

Objectif : **noter** la politique de cache du site (note sur 100, lettre,
six indicateurs), dire clairement **quelle politique il applique aujourd'hui**, ce que ça coûte au visiteur qui revient, ce qui est risqué
(anciens fichiers après une mise en ligne, session servie à quelqu'un d'autre),
et **quoi changer, où**, pour le visiteur anonyme comme pour le visiteur
connecté.

Arguments reçus : `$ARGUMENTS`

Dossier de cette skill noté `$K` (utiliser le chemin réel) ; le script est
`$K/scripts/audit_cache.mjs` (Node 18 ou plus, bibliothèque standard, aucun
paquet à installer). Répondre dans la langue de l'utilisateur.

## 0. Le site et son code

- **L'adresse** : celle donnée en argument ; sinon la déduire du projet ouvert
  (README, `CLAUDE.md`, `package.json` › `homepage`, configuration de
  déploiement, sitemap) et la confirmer en une ligne ; sinon la demander.
  Préférer la **production** : un serveur local n'a souvent ni le proxy ni le
  CDN qui compressent et posent une partie des en-têtes.
- **Le code** : si le dépôt du site est ouvert (ou cité), on s'en servira à
  l'étape 3 pour relier chaque règle à sa source. Sinon l'audit reste valable,
  les correctifs seront donnés par type de serveur.
- **Les API** : si le site appelle ses propres API (application en JavaScript),
  repérer 2 ou 3 adresses lues à chaque page (configuration, catalogue, profil
  — dans le code client ou l'onglet Réseau) pour les passer en `--api`.

Vérifier Node : `node -v` (18 ou plus). Absent ou trop ancien : le dire et
proposer de l'installer (gestionnaire de paquets ou nodejs.org) ; en attendant,
faire l'étape 1 à la main avec `curl -sSI` et `curl -H 'If-None-Match: …'`.

## 1. Mesurer, en visiteur anonyme

```bash
node "$K/scripts/audit_cache.mjs" <url> --pages 3 [--api /api/x,/api/y] \
  --json <dossier-temporaire>/cache.json --md <dossier-temporaire>/cache.md
```

Le script suit les redirections, lit la page, trouve tout ce qu'elle charge
(styles, scripts **et les modules qu'ils importent**, préchargements, images,
icônes, polices, `url()` des CSS), 3 autres pages du site, puis interroge
chaque fichier **deux fois** : normalement, puis avec ses validateurs pour
voir si le serveur répond 304. Il juge chaque réponse et estime ce qu'une
**deuxième visite dans l'heure** retélécharge.

**La note** (`score` dans le JSON, en tête du rapport Markdown) : six
indicateurs sur 100, mesurés sur les réponses du site lui-même (les fichiers
tiers sont listés, pas notés), chacun avec un statut — **bon** (≥ 85),
**à améliorer** (≥ 60), **critique** (en dessous) :

| Indicateur | Poids | Ce qui est mesuré |
|---|---|---|
| Réutilisation à la 2ᵉ visite | 30 | part des octets de la 1ʳᵉ visite qui ne sont **pas** retéléchargés à une 2ᵉ visite dans l'heure |
| Validateurs et 304 | 20 | pages et fichiers qui ont un ETag ou Last-Modified **et** répondent 304 quand rien n'a changé |
| Noms versionnés | 15 | octets des scripts, styles, polices et images dont le nom change avec le contenu |
| Durées adaptées | 15 | réponses gardées le bon temps : versionné → long, non versionné → court ou revalidé, pages → revalidées |
| Compression | 10 | réponses texte de plus de 1 Ko envoyées compressées |
| Sécurité | 10 | pas de session dans un cache partagé, pas de page ou script périmé après une mise en ligne, pas d'API qui mélange connecté et anonyme |

Note globale = moyenne pondérée des indicateurs mesurables ; lettre A ≥ 90,
B ≥ 75, C ≥ 60, D ≥ 40, E en dessous. Un cookie dans un cache partagé plafonne
la note à 39, quel que soit le reste. Sur un serveur local, l'indicateur
Compression est souvent à 0 (c'est le proxy de production qui compresse) :
le dire plutôt que de le compter comme un défaut.

Les constats (`findings`), du plus grave au moins grave :

| Code | Ce que ça veut dire |
|---|---|
| `PUBLIC_WITH_COOKIE` | Réponse qui pose un cookie tout en étant cachable par un cache partagé : risque de servir la session d'un visiteur à un autre. **Toujours en tête du rapport.** |
| `NO_VALIDATOR` | Revalidé à chaque visite (`no-cache`, `max-age=0`…) sans ETag ni Last-Modified : **retéléchargé en entier à chaque fois**. |
| `VALIDATOR_IGNORED` | Un validateur existe mais la requête conditionnelle répond encore 200 (proxy ou compression qui change l'ETag). |
| `LONG_UNVERSIONED` | Gardé longtemps (ou `immutable`) sous un nom qui ne change pas avec le contenu : après une mise en ligne, les visiteurs qui reviennent gardent l'ancien fichier. |
| `HTML_LONG` | Page HTML gardée plus de 5 min sans redemander : ancienne page (et anciens noms de fichiers) après une mise en ligne. |
| `NO_STORE_ASSET` | `no-store` sur un fichier du site : jamais gardé. |
| `NOT_COMPRESSED` | Texte envoyé sans gzip, br ou zstd. |
| `NO_CACHE_HEADER` | Aucun Cache-Control : le navigateur devine (≈ 10 % de l'âge du fichier). |
| `VERSIONED_SHORT` / `NOT_IMMUTABLE` | Nom versionné mais durée courte, ou sans `immutable` : occasion manquée. |
| `UNVERSIONED_REVALIDATED` | Sûr (304 quand rien n'a changé) mais un aller-retour par fichier à chaque visite. |
| `API_NOT_SHARED` / `API_CACHE_UNKEYED` | API jamais gardée (normal pour des données personnelles) ; ou API cachable sans `Vary: Authorization, Cookie`. |

Limites à garder en tête et à dire si elles comptent :
- Le script lit le HTML **envoyé par le serveur**. Un site qui se dessine en
  JavaScript charge d'autres images et appels après coup : ceux-là, l'étape 2
  les voit.
- Il ne se connecte jamais : la partie « connecté » vient de l'étape 3.
- L'heuristique « versionné » reconnaît `app.3f9a1c2e.js`, `app-BN3x8k2Q.js`,
  `?v=…`, `/_next/static/`, `/_astro/`… Un nom ambigu se vérifie dans le code
  (le nom change-t-il quand le contenu change ?).

## 2. Confirmer dans un vrai navigateur (si un outil de navigateur est disponible)

Un navigateur a aussi un cache mémoire et charge ce que le JavaScript ajoute.
Ouvrir la page, attendre la fin du chargement, **recharger**, puis lire
(sans les paramètres d'URL, qui peuvent contenir des données privées) :

```js
performance.getEntriesByType('resource').map(e =>
  `${new URL(e.name).pathname} transfer=${e.transferSize}B start=${Math.round(e.startTime)}ms end=${Math.round(e.responseEnd)}ms`).join('\n')
```

`transferSize` 0 = servi par le cache ; ~300 octets = un 304 ; la taille du
fichier = retéléchargé. Noter au passage la **chaîne de démarrage** (requêtes
qui s'attendent les unes les autres, même appel fait deux fois) : ce n'est pas
du cache, mais c'est souvent ce que l'utilisateur ressent comme « lent » ou
comme un écran intermédiaire au chargement ; le signaler en une ligne.

## 3. Trouver d'où vient chaque règle, et le cas « connecté »

Avec le dépôt, chercher où sont posés les en-têtes (adapter à la pile) :

| Pile | Où regarder |
|---|---|
| Caddy | `Caddyfile` : `header … Cache-Control`, `file_server` (pose ETag et Last-Modified), `encode` |
| nginx | `add_header Cache-Control`, `expires`, `etag`, `gzip`/`brotli` |
| Apache / hébergement mutualisé | `.htaccess` : `ExpiresByType`, `Header set Cache-Control`, `FileETag` |
| Node (http, Express, Fastify, Koa) | `cache-control`, `setHeader`, `express.static(… { maxAge, immutable, etag })`, serveur de fichiers maison |
| Next.js / Nuxt / Astro / Vite / Eleventy | `headers()` de `next.config`, nommage des fichiers au build (empreinte ou non), filtres de version |
| Vercel / Netlify / Cloudflare Pages | `vercel.json` › `headers`, `netlify.toml` / `_headers`, `_headers` ; règles de cache du CDN hors dépôt (le dire) |

Grep utile : `grep -rniE "cache-control|max-age|immutable|no-store|no-cache|etag|last-modified|expires" --exclude-dir=node_modules`.

**Visiteur connecté** — le déterminer dans le code, jamais en se connectant
avec les identifiants de l'utilisateur :
- Comment la session voyage-t-elle ? **Cookie** (le HTML et les API peuvent
  être personnalisés) ou **jeton `Authorization`** (le HTML est le même pour
  tous, seules les API varient).
- Quelles réponses changent selon l'utilisateur (page de compte, menu avec le
  pseudo, prix, droits, API `/me`) ?
- Ces réponses sont-elles `private` ou `no-store` ? Sinon, ou si une même
  adresse sert anonyme et connecté, ont-elles `Vary: Cookie` ou
  `Vary: Authorization` ?

## 4. La politique cible

Proposer cette grille, ajustée à ce qu'on a trouvé (c'est le « tout ou rien »
raisonnable : beaucoup de cache pour ce qui est commun à tous, aucun pour ce
qui est personnel) :

| Ressource | Anonyme | Connecté |
|---|---|---|
| Scripts, styles, polices **versionnés** (empreinte dans le nom ou `?v=<hash>`) | `public, max-age=31536000, immutable` | idem (identiques pour tous) |
| Scripts et styles **non versionnés** | `no-cache` + ETag/Last-Modified (304) — en attendant de les versionner | idem |
| Images | versionnées : 1 an `immutable` ; sinon `public, max-age=3600, stale-while-revalidate=86400` + validateur | idem |
| Pages HTML communes | `no-cache` + ETag (304 si inchangée) ; avec un CDN purgé à chaque mise en ligne : `s-maxage` court | si la session est un cookie et la page personnalisée : `private, no-cache` ou `no-store` ; sinon idem |
| API de données communes (catalogue, configuration) | `public, max-age=60, stale-while-revalidate=300` + `Vary: Authorization, Cookie` | `private, no-store` (ou `private, max-age` court si sans risque) |
| API personnelles (`/me`, panier, compte) | — | `private, no-store` |
| Réponses qui posent un cookie | jamais `public` | jamais `public` |
| Redirections | 301/308 définitives : peuvent être gardées (1 h à 1 j) ; 302/307 selon la langue ou la session : `no-store` + `Vary` adapté | idem |

Règles d'or à rappeler : on ne met `immutable` **que** sur un nom qui change
avec le contenu ; un `no-cache` **sans validateur** est un téléchargement
complet ; tout ce qui est personnel est `private`.

## 5. Le rapport

Dans la langue de l'utilisateur, court et concret :

1. **La note** : note sur 100, lettre et statut global, puis le tableau des
   six indicateurs (score, statut, une phrase sur ce qui le tire vers le
   bas). Après des correctifs, donner la note avant → après.
2. **La politique actuelle en une phrase**, puis le tableau par type
   (HTML, JS, CSS, images, polices, API, redirections) : en-têtes vus,
   validateur, 304 ou non.
3. **Ce que ça coûte** : poids de la première visite, poids retéléchargé à la
   deuxième (chiffres du script, confirmés par l'étape 2 si faite).
4. **Les risques**, du plus grave au moins grave (cookies partagés, fichiers
   périmés après mise en ligne), avec les fichiers concernés.
5. **Anonyme / connecté** : ce qui est fait aujourd'hui, ce qui devrait l'être
   (grille de l'étape 4).
6. **Les correctifs, par priorité**, chacun avec le fichier et la ligne à
   modifier (ou l'extrait de configuration pour la pile détectée), le gain
   attendu et **les points de note qu'il rapporte** (indicateur concerné).

Puis proposer de les appliquer. Si l'utilisateur accepte : faire les
changements, ajouter un test quand le projet en a, relancer le script (et
l'étape 2) sur l'environnement local, puis sur la production une fois
déployé, et montrer l'avant/après (note et lettre, poids de la deuxième visite,
constats disparus). Ne jamais déployer ni modifier une configuration de production
(proxy, CDN) sans accord explicite.

## Garde-fous

- Lecture seule tant que l'utilisateur n'a pas validé les correctifs.
- Ne jamais demander, saisir ni utiliser d'identifiants, cookies ou jetons de
  l'utilisateur pour tester la partie connectée : elle se déduit du code.
- Ne pas recommander `immutable` sur un fichier dont le nom ne change pas avec
  son contenu, même si « on ne le modifie jamais ».
- Rester raisonnable avec le site audité : le script fait au plus `--max`
  fichiers (150 par défaut), deux requêtes chacun, l'une après l'autre.

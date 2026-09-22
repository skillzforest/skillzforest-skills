---
name: av-schema-logique
description: >-
   Produit le schéma d'architecture LOGIQUE d'un projet (fichier .excalidraw) en partant d'un template bundlé, puis en l'ADAPTANT à la topologie réelle du projet. Le schéma montre les grandes briques (utilisateur, front, cœur applicatif, données, CDN, capacités, API tierces, exploitation) et la circulation de l'information, sans détail bas niveau (IP, ports, serveurs). Le skill a autonomie pour renommer les intitulés, retirer des briques, réaligner et restructurer selon que la cible est un SaaS sur-mesure headless, une plateforme couplée hébergée (type Shopify standard) ou une architecture headless sur plateforme commerce (type Hydrogen). Déclenche systématiquement ce skill dès que l'utilisateur veut produire, générer ou mettre à jour le schéma logique, l'architecture logique ou le diagramme logique d'un projet : « fais le schéma logique de X », « génère l'architecture logique de X ». Suite Avant-Vente SkillzForest (préfixe av-).
compatibility: Nécessite l'exécution de code (Node.js). Connecteur Google Drive pour déposer le fichier (optionnel).
---

# av-schema-logique — Schéma d'architecture logique (.excalidraw)

Génère le schéma LOGIQUE d'un projet en partant d'un template Excalidraw bundlé et en l'adaptant à la topologie cible. Sortie : un `.excalidraw` prêt à ouvrir, ajuster et exporter.

## Autonomie accordée

Le template est un POINT DE DÉPART et un vocabulaire visuel, pas un gabarit figé. Tu es autorisé et attendu à :
- RENOMMER les intitulés des briques pour coller au projet (`relabel` / `replace`).
- RETIRER les briques non pertinentes (`remove_by_text` / `remove_ids`) et masquer la redondance.
- RÉALIGNER les briques restantes (`align`) pour ne jamais laisser de trou après une suppression.
- RESTRUCTURER : quand la topologie cible diverge nettement du template, choisis le bon template de base (voir ci-dessous) ou reconstruis un `.excalidraw` avec le même vocabulaire visuel.

## Ce que le schéma doit montrer

Les grandes briques et la circulation de l'information : qui appelle quoi, dans quel sens, pour quel rôle. Toujours SANS détail bas niveau (pas d'IP, de port, de serveur, de capacité : ça, c'est le schéma physique). En revanche, NOMMER la plateforme structurante est légitime (« Boutique Shopify », « Front Hydrogen ») quand c'est elle qui détermine l'architecture. La cohérence prime sur la généricité : la topologie retenue doit être celle actée dans le cadrage plateforme (décision « couplé vs headless »).

## Templates de base et topologies

Deux templates sont bundlés. Choisir selon la topologie ACTÉE au cadrage plateforme :

1. `templates/architecture-logique.json` — SaaS sur-mesure, headless (défaut).
   Contenu : utilisateur (navigateur + app mobile sur l'API) ; couche d'entrée ; Frontend SSR ; API Métier en point d'entrée unique et surcouche des API tierces ; Données ; Assets ; CDN ; capacités reliées à l'API (IA/LLM, Worker, Webhook) ; encadré « API tierces » ; encadré « Exploitation ».

2. `templates/architecture-couplee.json` — plateforme couplée hébergée (type Shopify standard, sans développement).
   UNE seule brique centrale hébergée qui absorbe front, checkout, admin, commerce, données et CDN. AUCUNE flèche interne (pas de flèche API REST entre un front et un back). Ce cas ne se fabrique PAS en éditant le template headless : partir de ce template couplé. Ajustements typiques : relabel de la brique centrale au nom réel de la plateforme (« SHOPIFY — plateforme hébergée »), réduction de l'encadré « SERVICES EXTERNES » au réel (Paiement/PSP, Email/Newsletter, Analytics, consentement RGPD), note « Exploitation assurée par la plateforme ».

3. Headless sur plateforme commerce (type Shopify Hydrogen/Oxygen).
   Séparer le front du commerce : « Front Hydrogen (SSR, Oxygen/CDN) » en façade ; « Storefront API (GraphQL) » et, si besoin, un « BFF / couche métier » ; le back-office et le moteur commerce restent la plateforme hébergée (« Admin API »). Partir du template headless et relabeler, ou reconstruire. À ne retenir que si le cadrage a tranché pour du headless.

## Étape 1 — Préparer les éditions

Écrire `edits.json` (tous les champs optionnels) :
```json
{
  "title": "{Projet}",
  "relabel": [{ "find": "API REST Métier", "replace": "Commerce\ncatalogue · commandes" }],
  "replace": { "ancien": "nouveau" },
  "remove_by_text": ["QR CODE", "Machine Learning", "création job"],
  "remove_ids": ["db2"],
  "align": [{ "ids": ["svc0","svc1","svc2","svc3"], "grid": { "cols": 2, "gapx": 24, "gapy": 24 } }]
}
```
- `title` renseigne `Architecture logique — {Projet}`.
- `relabel` (ordonné) et `replace` (map) renomment. Recherche = SOUS-CHAÎNE sensible à la casse.
- CIBLAGE : les libellés sont souvent MULTI-LIGNES. Vise une sous-chaîne présente sur UNE seule ligne (ex. `"Machine Learning"`) ou insère un vrai `\n`. Une chaîne avec des espaces là où le bloc a un retour à la ligne ne matchera pas.
- `align` réaligne un groupe pour reboucher les trous (`axis: "x"`/`"y"` avec `gap`, ou `grid` avec `cols`).

## Étape 2 — Générer et balayer

```bash
node scripts/edit_excalidraw.js templates/<base>.json edits.json Schema_logique_{Projet}.excalidraw
```
Le moteur applique substitutions, suppressions et alignements, et garantit une sortie cohérente (flèches et références orphelines nettoyées).
OBLIGATOIRE : le moteur imprime en fin de run `Labels non rattachés à vérifier`. Examiner cette liste et rebalayer via `remove_by_text` tout label devenu orphelin (typiquement « création job », « REST/JWT », « headless » après suppression des briques associées). Un schéma livré ne contient AUCUN label suspendu.

## Étape 3 — Déposer et insérer

1. Déposer le `.excalidraw` dans `{Projet}/02_Cadrage plateforme/Schémas d'architecture` (sans conversion), ou le livrer à l'utilisateur.
2. Dire à l'utilisateur : ouvrir dans Excalidraw, ajuster si besoin, exporter en image (PNG/SVG) et l'insérer dans la note de cadrage plateforme, section 3 (emplacement ▢). Insertion manuelle.

## Garde-fous

- Template intouché : on édite vers un fichier de sortie, jamais le template.
- Choisir le template de base selon la topologie ACTÉE au cadrage plateforme ; ne pas réintroduire de briques hors périmètre.
- Niveau logique uniquement : pas d'IP, de port ni de serveur. Nommer la plateforme structurante est permis.
- Dans un cadre, des cartes de même niveau partagent la même ligne ou colonne, avec des gaps constants. Jamais de trou.
- Aucun label orphelin dans la sortie (vérifier le rapport du moteur).

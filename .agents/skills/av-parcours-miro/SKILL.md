---
name: av-parcours-miro
description: >-
  Construit le user story mapping des parcours utilisateurs sur Miro à partir du cadrage fonctionnel du projet : duplique le board template, puis l'ajuste automatiquement (backbone = boucle de valeur, colonnes de priorité Must have / Nice to have / Extra, cartes = user stories, regroupées par persona). Renvoie l'URL du nouveau board. Déclenche systématiquement ce skill dès que l'utilisateur veut construire, générer ou mettre à jour les parcours utilisateurs, le user story mapping ou les parcours personas d'un projet — « construis les parcours de X », « fais le user story mapping de X », « génère les parcours personas sur Miro ». À l'issue, préciser à l'utilisateur que c'est à lui de copier l'URL du board dans le doc de cadrage fonctionnel. Suite Avant-Vente AI Factory (préfixe av-).
compatibility: Nécessite le connecteur Miro. Lit le cadrage fonctionnel via le connecteur Google Drive.
---

# av-parcours-miro — Parcours utilisateurs (user story mapping) sur Miro

Traduit le cadrage fonctionnel d'un projet en un **user story mapping** sur Miro : duplique le board template et l'ajuste automatiquement au projet. Compagnon du cadrage fonctionnel (rôle 4 — UX).

## Board template

`https://miro.com/app/board/uXjVHzQNQuU=/` — **ne jamais le modifier**. On travaille toujours sur une **copie**.

## Convention de mapping

- **Backbone** (colonnes, de gauche à droite) = les étapes de la **boucle de valeur** du cadrage fonctionnel.
- **Lignes / priorités** = **Must have** (le parcours lui-même), **Nice to have**, **Extra**.
- **Cartes** = user stories (« En tant que … je veux … afin de … »).
- **Regroupement par persona** = selon la structure du template (une section / frame par persona). Suivre la convention réellement présente dans le template dupliqué.

## Étape 1 — Récupérer la matière (périmètre projet STRICT)

Résoudre le dossier du projet sous `02_PROSPECTS` (parent `1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q`) : `search_files` `title contains '{Projet}'` **filtré** `mimeType = 'application/vnd.google-apps.folder'` **et** `'1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q' in parents`. Lire le cadrage fonctionnel dans `{Projet}/01_Cadrage fonctionnel` uniquement (jamais un autre projet).

En extraire : **personas**, **boucle de valeur** (backbone), et les **user stories** classées Must / Nice / Extra. Si ces éléments manquent, les demander à l'utilisateur ou proposer de lancer `av-cadrage-fonctionnel` d'abord. **Ne rien inventer** : une story absente reste `[à compléter]`.

## Étape 2 — Dupliquer le template

1. **Tentative automatique** : lire le template (`layout_read`) pour comprendre sa structure, créer un nouveau board (`board_create`) nommé `Parcours_{Projet}`, et y reproduire la structure du template.
2. **Filet fiable (recommandé si la duplication auto n'est pas fidèle)** : demander à l'utilisateur de dupliquer le template dans Miro (menu du board → **Duplicate**, 1 clic) et de coller l'URL du nouveau board. Poursuivre l'ajustement sur cette URL.

Dans les deux cas, la suite s'applique à la **copie**, jamais au template.

## Étape 3 — Ajuster la copie au cadrage

1. `layout_read` (ou `board_list_items`) la copie pour identifier sa structure réelle : colonnes du backbone, swimlanes de priorité, cartes/sticky notes, sections par persona.
2. Remplacer le contenu générique du template par celui du projet :
   - renommer les colonnes du backbone avec les étapes de la boucle de valeur ;
   - pour chaque persona, placer ses user stories dans les bonnes lignes (Must / Nice / Extra) ;
   - utiliser `layout_update` (find/replace sur le DSL) pour les cartes/sticky notes, ou `table_sync_rows` si le mapping est un tableau.
3. Rester fidèle à la charte du template (couleurs, disposition) : n'ajuster que le **contenu**, pas la mise en forme.

## Étape 4 — Restituer et consigner l'URL

1. `board_show` la copie pour l'afficher.
2. Donner l'**URL du nouveau board** à l'utilisateur.
3. **Dire explicitement à l'utilisateur que c'est à LUI de copier cette URL dans le doc de cadrage fonctionnel**, section 6 « Parcours utilisateurs » (`[Lien_board]`). **Le skill ne modifie pas le document de cadrage** — il ne fait que fournir l'URL.

## Garde-fous

- **Périmètre projet strict** : ne lire que le cadrage fonctionnel de CE projet.
- **Template intouchable** : toujours travailler sur une copie.
- **Aucune modification du doc Drive** : le report de l'URL dans le cadrage fonctionnel est une action **manuelle** de l'utilisateur.
- **Ne rien inventer** : les parcours et stories viennent du cadrage ; les manques sont signalés, pas comblés.

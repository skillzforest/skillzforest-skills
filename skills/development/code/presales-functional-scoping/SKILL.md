---
name: presales-functional-scoping
description: >-
  Produit une note de cadrage fonctionnel à la charte (Google Doc) à partir du cahier des charges et des documents client. Le skill analyse le besoin puis remplit le master : compréhension du besoin, boucle de valeur, partis-pris tranchés, cadrage détaillé par thème (« ma lecture / mon parti-pris / à valider »), parcours utilisateurs, démo. Rédigé à la première personne (Arnaud), en support de décision : il challenge et recommande, n'invente jamais, et signale les incertitudes « à valider ». Le document est déposé dans le dossier 01_Cadrage fonctionnel du projet. Déclenche systématiquement ce skill dès que l'utilisateur veut cadrer le besoin fonctionnel, produire un cadrage fonctionnel, ou analyser un cahier des charges — « fais le cadrage fonctionnel de X », « cadre le besoin de X », « analyse ce CDC ». Suite Avant-Vente SkillzForest (préfixe presales-).
compatibility: Nécessite l'exécution de code (Node.js) avec le paquet `docx`, et le connecteur Google Drive pour le dépôt.
---

# presales-functional-scoping — Note de cadrage fonctionnel

Transforme un cahier des charges et des documents client en une note de cadrage fonctionnel de qualité conseil : un **support de décision**, pas un cahier des charges. Deux couches : **analyser** le besoin (raisonnement), puis **produire** le document rempli (charte + dépôt).

## Règle absolue

- **Ne jamais inventer.** Toute zone incertaine est explicitement signalée « à valider » ; un champ sans matière reste `[à compléter]`.
- **Voix à la première personne** (Arnaud) : « ma lecture », « je recommande », « mon parti-pris ».
- **Challenger et recommander** : ce n'est pas une restitution neutre du CDC, mais une prise de position argumentée.
- **Zones client laissées vides** : les lignes « Avis du client » et les encadrés violets « Réponse du client » ne sont jamais pré-remplis.

## Étape 1 — Entrées et analyse

### Périmètre STRICT au projet courant (règle de scoping)

Avant toute lecture, **résoudre le dossier racine du projet** sous `02_PROSPECTS` (parent `1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q`) : `search_files` sur `title contains '{Projet}'` **filtré** `mimeType = 'application/vnd.google-apps.folder'` **et** `'1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q' in parents`. En cas de plusieurs correspondances, demander lequel.

Ensuite, **ne lire QUE les documents de l'arborescence de CE projet**, en ciblant chaque sous-dossier par son `id` :

- **CDC et documents client** → `{Projet}/00_Entrées client`
- **Comptes rendus** → `{Projet}/03_Comptes rendus`  *(les CR du projet nourrissent l'analyse : décisions actées, points en suspens)*
- **Version existante** (si itération) → `{Projet}/01_Cadrage fonctionnel`

Confiner **toutes** les recherches/listes aux enfants directs de ces dossiers via `'{folderId}' in parents`. **Ne jamais** utiliser de recherche globale `title contains` sans contrainte de parent : elle capterait les fichiers d'un **autre** projet. Tout document situé hors de `{Projet}/` est **ignoré** — y compris un CR portant un nom proche mais rangé ailleurs.

### Entrées complémentaires

Fichiers joints à la conversation (le cas échéant) et décisions déjà validées dans le projet — ne pas ré-arbitrer ce qui est acté.

**Analyse à produire** (application des rôles 1 à 4 de la doctrine — Business Analyst, Cadrage, PO/MVP, UX) :

- **Compréhension du besoin** — 2 à 4 phrases : problème métier, cible/persona principal, contrainte structurante (prix, modèle, canal). Reformuler, ne pas recopier le CDC.
- **Boucle de valeur** — 4 à 5 étapes, de la collecte à la mesure. C'est le fil rouge qui justifie les arbitrages MVP.
- **Partis-pris structurants** — 5 à 7 affirmations courtes et tranchées, chacune avec une justification de 1 à 2 phrases (ce qu'elle implique et ce qu'elle exclut).
- **Cadrage par thème** — adapter les thèmes au projet (ne pas garder le squelette générique tel quel). Pour chaque thème, une ou plusieurs lignes : `theme`, `lecture` (constat), `partiPris` (recommandation), `aValider` (question à trancher).
- **Parcours utilisateurs** — résumer en une phrase les parcours par persona. Ce skill **ne construit pas** le mapping : le user story mapping est produit sur Miro par le skill `presales-user-journey-miro`. Renseigner le lien du board s'il existe, sinon laisser `[Lien_board]`.
- **Démo** — l'URL de la démo si elle existe.

## Étape 2 — Génération

1. Écrire l'analyse dans `analysis.json` (schéma ci-dessous).
2. Générer :
   ```bash
   node scripts/build_cadrage_fonctionnel.js <analysis.json> <sortie.docx>
   ```
   Le moteur applique la charte, gère un nombre variable de partis-pris et de thèmes, retire la bannière « mode d'emploi » (version remplie) et laisse vides les zones d'annotation client.
3. Contrôler visuellement (PDF + rasterisation) avant dépôt.

**Schéma `analysis.json`** (tout champ absent ⇒ `[à compléter]`) :
```json
{
  "projet": "…", "version": "0.1",
  "comprehension": ["…", "…"],
  "boucle": ["Étape 1", "Étape 2", "Étape 3", "Mesure"],
  "partisPris": [{"titre": "…", "justification": "…"}],
  "themes": [
    {"titre": "5.1 …", "rows": [{"theme":"…","lecture":"…","partiPris":"…","aValider":"…"}]}
  ],
  "parcours": {"description": "…", "board_url": "…"},
  "demo_url": "…"
}
```

## Étape 3 — Dépôt dans Drive

1. Retrouver le dossier du projet sous `02_PROSPECTS` (parent `1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q`) puis son sous-dossier `01_Cadrage fonctionnel`.
2. Téléverser le `.docx` **avec conversion** en Google Doc (`create_file`, contenu docx base64, `parentId` du sous-dossier, sans désactiver la conversion).
3. **Nom** : `Cadrage_fonctionnel_{Projet}`. S'il existe déjà (copie déposée à l'init), proposer de le remplacer/versionner plutôt que d'empiler des doublons.
4. Restituer le lien.

Si le projet n'existe pas dans Drive, proposer d'abord `presales-init-project`, ou livrer le `.docx`.

## Garde-fous

- **Validation avant dépôt** : présenter la synthèse de l'analyse (compréhension, partis-pris, thèmes) pour accord avant génération.
- **Cohérence chaîne** : les décisions prises ici doivent rester cohérentes avec le cadrage plateforme et le chiffrage.
- **Master intouché** : le skill génère un document ; il ne modifie jamais le gabarit.

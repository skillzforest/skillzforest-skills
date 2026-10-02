---
name: presales-platform-scoping
description: >-
  Produit une note de cadrage technique de la plateforme à la charte (Google Doc) à partir des documents techniques du projet (architecture cible, décisions). Le skill tranche les décisions structurantes (headless vs couplé, multi-tenant, hébergement…), puis remplit les tableaux — composants techniques, matrice de flux, composants serveurs et chiffrage, services tiers — et la synthèse budgétaire, avec deux emplacements réservés aux schémas (logique et physique). Le document est déposé dans 02_Cadrage plateforme du projet. Déclenche systématiquement ce skill dès que l'utilisateur veut cadrer la plateforme technique, produire un cadrage technique/plateforme, ou une note d'architecture et de chiffrage infra — « fais le cadrage plateforme de X », « cadrage technique de X », « la note technique de X ». Suite Avant-Vente SkillzForest (préfixe presales-).
compatibility: Nécessite l'exécution de code (Node.js) avec le paquet `docx`, et le connecteur Google Drive pour le dépôt.
---

# presales-platform-scoping — Note de cadrage technique de la plateforme

Transforme les documents techniques d'un projet en une note de cadrage plateforme de qualité conseil : décisions tranchées, composants, flux, serveurs, services tiers et budget indicatif. Distincte du cadrage fonctionnel. Deux couches : **cadrer** (raisonnement, rôle 5) puis **produire** (charte + dépôt).

## Règles

- **Repartir des décisions déjà validées** dans les documents techniques du projet (architecture cible, décisions/hypothèses). **Ne pas ré-arbitrer** ce qui est acté.
- **Ne jamais inventer de chiffres.** Les coûts sont des **estimations** ; à défaut de valeur, laisser les placeholders `[€ …]` / `[… j/h]`. Ils seront consolidés avec les devis hébergeur et fournisseurs (et avec le futur skill `presales-quote`).
- **Décision structurante à trancher** : headless vs couplé (et, si pertinent, cloud managé vs VM, multi-tenant). Rendre **une recommandation unique**, justifiée par 2-3 critères, avec sa **condition de remise en cause**. Défaut pour un SaaS moderne : **headless**, API métier en surcouche, front SSR découplé, mobile branché sur l'API.

## Étape 1 — Entrées et analyse (périmètre projet STRICT)

Résoudre le dossier du projet sous `02_PROSPECTS` (parent `1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q`) : `search_files` `title contains '{Projet}'` **filtré** `mimeType = 'application/vnd.google-apps.folder'` **et** `'1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q' in parents`. Ne lire que les documents de CE projet (`{Projet}/00_Entrées client`, docs techniques du projet, version existante dans `{Projet}/02_Cadrage plateforme`), en confinant les recherches par `'{folderId}' in parents`. Jamais un autre projet.

**Analyse à produire** (rôle 5 — Architecte/CTO) : décisions structurantes ; référentiel des composants ; dimensionnement serveurs ; services tiers ; matrice de flux ; synthèse budgétaire. Les **deux schémas** (logique et physique) ne sont pas produits ici : ils sont générés par `presales-logical-diagram` / `presales-physical-diagram`, exportés en image, puis insérés aux emplacements `▢` (voir Étape 4).

## Étape 2 — Génération

1. Écrire l'analyse dans `analysis.json` (schéma ci-dessous).
2. Générer :
   ```bash
   node scripts/build_cadrage_plateforme.js <analysis.json> <sortie.docx>
   ```
   Le moteur applique la charte, gère des tableaux dynamiques, calcule les lignes de total (fusionnées) et conserve les deux encadrés d'insertion de schéma.
3. Contrôler visuellement (PDF + rasterisation) avant dépôt.

**Schéma `analysis.json`** (tout champ absent ⇒ placeholder) :
```json
{
  "projet": "…", "version": "0.1",
  "decisions":  [{"decision":"…","choix":"…","justification":"…","condition":"…"}],
  "composants": [{"composant":"…","techno":"…","version":"…","hebergement":"…","serveur":"…"}],
  "serveurs":   [{"composant":"…","type":"…","dim":"…","qte":"…","cout":"[€ …]"}],
  "serveurs_total": "[€ … / mois]", "serveurs_miseenplace": "[€ … one-shot]",
  "services":   [{"categorie":"…","integration":"…","tarif":"…","cout":"[€ …]","criticite":"…"}],
  "services_total": "[€ … / mois]", "services_integration": "[… j/h]",
  "budget": {"serveurs_mois":"…","services_mois":"…","total_mois":"…","miseenplace":"…","integration":"…"},
  "flux":       [{"id":"F1","source":"…","destination":"…","protoport":"HTTPS · 443","sens":"client →"}]
}
```

## Étape 3 — Dépôt dans Drive

1. Cibler `{Projet}/02_Cadrage plateforme` (par `id`).
2. Téléverser le `.docx` **avec conversion** en Google Doc (`create_file`, contenu docx base64, `parentId`, sans désactiver la conversion).
3. **Nom** : `Cadrage_plateforme_{Projet}`. S'il existe (copie déposée à l'init), proposer de remplacer/versionner.
4. Restituer le lien.

## Étape 4 — Insertion des schémas (manuelle)

Les images des schémas **logique** et **physique** (produites par `presales-logical-diagram` / `presales-physical-diagram`, exportées depuis Excalidraw) ne peuvent pas être insérées automatiquement dans le Google Doc. **Indiquer à l'utilisateur que c'est à lui d'insérer les deux images** aux emplacements `▢` des sections 3 et 5.

## Garde-fous

- **Périmètre projet strict** ; **décisions actées non ré-arbitrées** ; **aucun chiffre inventé**.
- **Cohérence chaîne** : les composants serveurs et services tiers alimenteront le devis (`presales-quote`).
- **Master intouché** : le skill génère un document ; il ne modifie jamais le gabarit.

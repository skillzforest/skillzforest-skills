---
name: av-presentation-client
description: >-
  Assemble la présentation client d'un projet (Google Slides) à partir du master de 28 slides : copie le master dans 05_Présentation client, puis renseigne les placeholders en agrégeant les livrables du projet (cadrage fonctionnel, cadrage plateforme, devis, parcours Miro, démo). Le deck résume le projet — executive summary, compréhension du besoin, vision produit, personas, périmètre, MVP, roadmap, planning, budget, TMA, risques — avec des slides CORE (toujours présentes) et OPTIONAL (à inclure selon le projet). Déclenche systématiquement ce skill dès que l'utilisateur veut produire la présentation client, le deck de proposition, ou assembler la soutenance d'avant-vente — « fais la présentation de X », « le deck client pour X », « assemble la proposition de X ». Suite Avant-Vente SkillzForest (préfixe av-).
compatibility: Connecteur Google Drive (copie + dépôt). Pour l'auto-remplissage des slides, un connecteur Google Slides (ex. via Composio) est nécessaire ; sinon, remplissage manuel guidé (recommandé d'activer le connecteur vu le nombre de slides).
---

# av-presentation-client — Présentation client (Google Slides)

Assemble le deck de proposition d'un projet à partir du master de 28 slides : on **copie** le master, on **agrège** les livrables déjà produits, et on **remplit les placeholders**. C'est l'étape d'assemblage (Rôle 9) : elle ne réinvente rien, elle synthétise.

## Master

`Master présentation` — fileId `17Ys_cXmWcPpD1hcaW_VpbTGzFyRNhth1M3phGTaq7AY`. **Ne jamais le modifier** : on travaille sur une copie.

## Principe du master

- **28 slides**, chacune avec un **titre**, un sous-titre, une **pastille CORE / OPTIONAL**, des **placeholders `[…]`**, un pied « DataToForm AI · Confidentiel » et un numéro.
- **Slides CORE** : toujours présentes. **Slides OPTIONAL** (ex. *Infrastructure / Cloud* n°14, *SEO · Performance · Analytics* n°20) : à conserver ou retirer selon la pertinence pour le projet.
- Slides clés à alimenter : titre (n°01), **Executive Summary** (02), Compréhension (03), Vision (04), Personas (05), Périmètre (06), User Journey (07), **MVP** (08), Roadmap (09), UX (10), **Démo** (11), Architectures (12-13), **Planning** (23), **Budget** (24), Risques (25), Run (26), **Maintenance & TMA** (27).

## Étape 1 — Périmètre projet STRICT et agrégation

Résoudre le dossier du projet sous `02_PROSPECTS` (parent `1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q`) : `search_files` `title contains '{Projet}'` **filtré** `mimeType = 'application/vnd.google-apps.folder'` **et** `'1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q' in parents`. Ne lire que les livrables de CE projet.

Agréger la matière depuis :
- **`01_Cadrage fonctionnel`** → compréhension, vision, personas, périmètre, MVP, parcours ;
- **`02_Cadrage plateforme`** → architectures, sécurité, infra, budget infra récurrente ;
- **`04_Devis`** → budget forfait (slide 24) et **TMA** (slide 27) ;
- **parcours Miro** (URL dans le fonctionnel) → User Journey ;
- **démo** (URL GitHub Pages) → slide 11.

**Ne rien inventer** : chaque placeholder est rempli depuis un livrable existant ; à défaut, le laisser `[…]` et le signaler.

## Étape 2 — Copier le master

`copy_file` du master vers `{Projet}/05_Présentation client`, titre `Presentation_{Projet}`.

## Étape 3 — Choisir les slides OPTIONAL

Décider, avec l'utilisateur, quelles slides OPTIONAL conserver (ex. Infrastructure, SEO) selon le projet. Retirer les autres de la copie.

## Étape 4 — Renseigner les placeholders

Remplacer les `[…]` par le contenu agrégé (client, date, exec summary, personas, MVP, planning, budget, TMA…).
- **Si un connecteur Google Slides est disponible** (ex. Composio) : écrire dans les slides de la copie (remplacement de texte des placeholders). Conserver mise en page, pastilles et notes.
- **Sinon** : fournir à l'utilisateur le **mapping placeholder → valeur** par slide (remplissage manuel). Vu le volume, recommander d'activer un connecteur Slides.

## Étape 5 — Restituer

Donner le lien du deck. Rappeler de vérifier la cohérence des chiffres (budget/planning/TMA) avec le devis et le cadrage plateforme, et d'insérer les visuels (maquettes, schémas, aperçu démo) là où le master les prévoit.

## Garde-fous

- **Master intouché** ; on remplit une copie.
- **Cohérence chaîne** : budget = devis ; TMA = devis TMA ; archi = cadrage plateforme ; parcours = board Miro. Aucun chiffre ni engagement inventé.
- **Slides OPTIONAL** retirées si non pertinentes, pour un deck resserré.

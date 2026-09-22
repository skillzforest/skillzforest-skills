---
name: av-devis
description: >-
  Produit le devis d'un projet à partir du master Google Sheet « Devis_Modulaire_MASTER » : copie le master dans 04_Devis, puis renseigne les cellules d'entrée (client, n° de devis, date, et par ligne : Inclure ? / Jours / Type / TJM). Le devis est modulaire — les colonnes « Inclure ? » (Oui/Non) et « Jours » pilotent seules Montant HT, sous-totaux par lot, socle/options, TOTAL HT, TVA 20 % et TTC ; l'échéancier 30/40/30, la validité +30 jours et les exclusions sont déjà en place. Déclenche systématiquement ce skill dès que l'utilisateur veut produire un devis, chiffrer un projet, ou consolider les charges et coûts d'un projet — « fais le devis de X », « chiffre le projet X », « le devis pour X ». Suite Avant-Vente SkillzForest (préfixe av-).
compatibility: Connecteur Google Drive (copie + dépôt). Pour l'auto-remplissage des cellules, un connecteur Google Sheets (ex. via Composio) est nécessaire ; sinon, saisie manuelle guidée.
---

# av-devis — Devis modulaire du projet

Génère le devis d'un projet à partir du master modulaire, déposé dans `04_Devis`. On **copie** le master et on **remplit uniquement les cellules d'entrée** : toutes les formules (Montant HT, sous-totaux, socle/options, TOTAL HT / TVA / TTC, échéancier, validité) se recalculent seules.

## Master

`Devis_Modulaire_MASTER` — fileId `1xst-cet8BlSh8-Cp7oa4zFI1wUr0ySS4REAf9uDRXo8`. **Ne jamais le modifier** : on travaille sur une copie.

## Principe du master (à respecter)

- **3 leviers d'entrée** par ligne : **Inclure ?** (Oui = retenu et compté · Non = proposé mais grisé/écarté), **Jours**, **TJM** (défaut 600 €). Tout le reste est calculé.
- **Lots** : 1 Cadrage & Architecture · 2 Pilotage & Suivi Agile · 3 Créative & UI/UX · 4 Développement assisté par IA · 5 DevOps & Infrastructure · 6 Refacturation & Licences (forfait) · OPTION (par défaut « Non »).
- **Types** : Cadrage, Pilotage, Design, Dev IA, QA, Revue, DevOps, Licences.
- **Règle QA** : les lignes de tests/QA valent **25 % du dev** associé.
- Échéancier **30/40/30**, **validité +30 jours**, TVA 20 %, exclusions et bloc signature : déjà dans le master.
- La **« Note interne »** en bas est à **retirer avant envoi** au client.

## Étape 1 — Périmètre projet STRICT et matière

Résoudre le dossier du projet sous `02_PROSPECTS` (parent `1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q`) : `search_files` `title contains '{Projet}'` **filtré** `mimeType = 'application/vnd.google-apps.folder'` **et** `'1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q' in parents`. Ne lire que les documents de CE projet.

Constituer la matière de chiffrage à partir de :
- **`{Projet}/02_Cadrage plateforme`** → charges serveurs/DevOps (Lot 5) et coûts fixes / licences (Lot 6) ;
- **`{Projet}/01_Cadrage fonctionnel`** → périmètre, UX (Lot 3), dev (Lot 4) ;
- roadmap / pilotage → Lots 1 et 2.

**Ne rien inventer** : les jours et charges viennent du cadrage. En l'absence de matière, proposer des jours par défaut **clairement signalés comme à valider**.

## Étape 2 — Copier le master

`copy_file` du master vers `{Projet}/04_Devis`, titre `Devis_{Projet}`. La copie conserve formules et mise en forme.

## Étape 3 — Proposer le contenu (validation)

Construire la liste des lignes par lot (description, type, jours, Inclure ?) à partir de la matière projet, TJM 600 € par défaut, QA = 25 % du dev. **Présenter ce tableau à l'utilisateur pour validation** (jours, inclusions, options) avant d'écrire.

## Étape 4 — Renseigner les cellules d'entrée

Cibles : bloc **DESTINATAIRE** (nom/société, adresse, CP-ville, contact) ; **N° de devis** et **Date** (la validité se calcule) ; par ligne : **Inclure ?**, **Description**, **Type**, **Jours** (et TJM si ≠ 600).

- **Si un connecteur Google Sheets est disponible** (ex. Composio) : lire la copie pour localiser les cellules d'entrée, puis y écrire les valeurs. Ne pas toucher aux colonnes calculées (Montant HT, sous-totaux, totaux).
- **Sinon** : fournir à l'utilisateur la **liste exacte cellule → valeur** à saisir (le master est conçu pour cette saisie rapide), et lui rappeler que les totaux se recalculent seuls.

Pour ajouter une ligne dans un lot, l'insérer **dans** la plage du lot (le sous-total s'étend automatiquement).

## Étape 5 — Restituer

Donner le lien du devis. Rappeler : vérifier les inclusions/jours, **retirer la « Note interne »** avant envoi, et que socle vs options apparaissent séparément.

## Garde-fous

- **Master intouché** ; on remplit une copie.
- **Ne rien inventer** : jours/charges issus du cadrage ; défauts signalés « à valider ».
- **Ne pas écraser les formules** : n'écrire que dans les cellules d'entrée.
- **Cohérence chaîne** : le devis consolide les charges (dev, pilotage, DevOps) et les coûts fixes (services tiers, licences) déjà cadrés dans la note plateforme.

## Masters locaux (mode "scaffold / dry-run")

Pour faciliter les tests locaux et les intégrations hors-MCP, ce répertoire peut contenir un dossier `masters/` avec les fichiers maîtres (`Devis_Modulaire_MASTER.xlsx`, `Devis_Modulaire_MASTER.docx`, `Devis_Modulaire_MASTER.pptx`). Le workflow local proposé :

- déposer le master dans `skills/sales/av-devis/masters/` (ne pas modifier le master original)
- fournir un fichier `mappings.json` décrivant quelles cellules/places du master correspondent aux champs d'entrée (ex. `"DESTINATAIRE!B2": "client"`). Un exemple est fourni `mappings.example.json`.
- lancer le script local pour une exécution dry-run : `node scripts/fill_devis.js --project "MonProjet" --master masters/Devis_Modulaire_MASTER.xlsx --data sample_input.json --out out/`

Le script fait une copie du master en `out/Devis_{Projet}.xlsx` et tente d'appliquer les valeurs fournies via `--data` selon `mappings.json`. Si aucun mapping n'existe, le script crée la copie et affiche la liste des champs attendus pour faciliter la saisie manuelle.

Ce mode permet à un acheteur d'intégrer les masters fournis avec la skill et d'exécuter localement sans accès Drive. Pour une intégration Drive/MCP complète, le même principe s'applique mais la copie se fait via `copy_file` et l'écriture via le connecteur Sheets/Drive.

Note importante : la skill `av-devis` est conçue pour être invoquée par conversation/prompt (UX habituel). Le script `fill_devis.js` (ou le script générique `scripts/fill_master.js`) est un utilitaire local destiné aux tests et aux intégrations automatisées côté développeur — ce n'est pas le canal principal d'usage pour un utilisateur final.

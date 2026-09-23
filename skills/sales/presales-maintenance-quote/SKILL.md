---
name: presales-maintenance-quote
description: >-
  Produit le devis de TMA (Tierce Maintenance Applicative) d'un projet à partir du master Google Sheet « Devis TMA » : copie le master dans 04_Devis, puis renseigne les cellules d'entrée (client, n° de devis, date, et par ligne : Inclure ? / Jours par mois / TJM). Devis récurrent modulaire — les colonnes « Inclure ? » (Oui/Non) et « Jours / mois » pilotent seules les coûts mensuels, annuels (×12), sous-totaux par type, TOTAL HT, TVA 20 % et TTC ; l'engagement 12 mois, les modalités et exclusions sont déjà en place. Déclenche systématiquement ce skill dès que l'utilisateur veut produire un devis de maintenance, un devis TMA, ou chiffrer la maintenance récurrente d'un projet — « fais le devis TMA de X », « chiffre la maintenance de X », « le contrat de maintenance pour X ». Suite Avant-Vente SkillzForest (préfixe presales-).
compatibility: Connecteur Google Drive (copie + dépôt). Pour l'auto-remplissage des cellules, un connecteur Google Sheets (ex. via Composio) est nécessaire ; sinon, saisie manuelle guidée.
---

# presales-maintenance-quote — Devis de maintenance récurrente (TMA)

Génère le devis de TMA d'un projet à partir du master modulaire récurrent, déposé dans `04_Devis`. On **copie** le master et on **remplit uniquement les cellules d'entrée** ; tous les coûts (mensuels, annuels, sous-totaux, totaux, TVA) se recalculent seuls.

## Master

`Devis TMA` — fileId `1aIomu6BFRSiU0j093mu91_ioeqEeiLIunjYTT931BOw`. **Ne jamais le modifier** : on travaille sur une copie.

## Principe du master (à respecter)

- **Prestation récurrente** : facturation mensuelle à terme échu, engagement 12 mois (tacite reconduction, révisable annuellement).
- **3 leviers d'entrée** par ligne : **Inclure ?** (Oui = retenu · Non = grisé/écarté), **Jours / mois**, **TJM** (défaut 600 €). Coût mensuel HT et coût annuel (×12) calculés.
- **4 types de TMA**, chacun avec 3 lignes (prestation · **déploiement** · **recette/QA**) :
  - **CORRECTIVE** — anomalies & non-régression
  - **ADAPTATIVE** — montées de version & compatibilité
  - **ÉVOLUTIVE** — évolutions mineures & améliorations
  - **PRÉVENTIVE** — supervision & sécurité (**option**, défaut « Non »)
- Récapitulatif par type + **TOTAL HT / TVA 20 % / TTC** (mensuel et annuel), modalités, exclusions et bloc signature : déjà dans le master.
- **Volumétries = hypothèses** en jours-homme/mois, à ajuster ; SLA en annexe si requis.
- La **« Note interne »** en bas est à **retirer avant envoi**.

## Étape 1 — Périmètre projet STRICT et matière

Résoudre le dossier du projet sous `02_PROSPECTS` (parent `1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q`) : `search_files` `title contains '{Projet}'` **filtré** `mimeType = 'application/vnd.google-apps.folder'` **et** `'1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q' in parents`. Ne lire que les documents de CE projet.

Matière de chiffrage : le **cadrage plateforme** (`{Projet}/02_Cadrage plateforme`) — exploitation/run, complexité, services tiers — et le périmètre fonctionnel donnent les hypothèses de volumétrie par type. **Ne rien inventer** : les jours/mois sont des hypothèses **explicitement signalées « à valider »**.

## Étape 2 — Copier le master

`copy_file` du master vers `{Projet}/04_Devis`, titre `Devis_TMA_{Projet}`. La copie conserve formules et mise en forme.

## Étape 3 — Proposer le contenu (validation)

Proposer, par type de TMA, les jours/mois (prestation, déploiement, recette/QA) et les inclusions (préventive en option). **Présenter à l'utilisateur pour validation** avant d'écrire.

## Étape 4 — Renseigner les cellules d'entrée

Cibles : bloc **DESTINATAIRE** ; **N° de devis** et **Date** ; par ligne : **Inclure ?**, **Jours / mois** (et TJM si ≠ 600).
- **Si un connecteur Google Sheets est disponible** : lire la copie pour localiser les cellules d'entrée, puis y écrire les valeurs (ne pas toucher aux colonnes calculées : coûts mensuel/annuel, sous-totaux, totaux).
- **Sinon** : fournir la **liste exacte cellule → valeur** à saisir (le master est fait pour ça).

## Étape 5 — Restituer

Donner le lien du devis TMA. Rappeler : vérifier inclusions/volumétries, **retirer la « Note interne »**, et que la TMA préventive est une option (défaut « Non »).

## Garde-fous

- **Master intouché** ; on remplit une copie.
- **Ne rien inventer** : volumétries = hypothèses signalées « à valider ».
- **Ne pas écraser les formules** : n'écrire que dans les cellules d'entrée.
- **Cohérence chaîne** : la TMA prolonge le projet chiffré au forfait (devis) ; les refontes majeures restent hors TMA.

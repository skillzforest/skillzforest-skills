# Workflow : cadrage fonctionnel

## Objectif

Transformer les entrées client et les documents du projet en une note de cadrage fonctionnel claire, argumentée et exploitable pour la suite du projet.

## Entre dans le workflow

Le workflow démarre quand :
- un nouveau projet est créé via `av-init-projet`, ou
- un projet existant a déjà des documents client et des CRs, ou
- un besoin métier doit être formalisé avant le chiffrage.

## Skill principale

- `av-cadrage-fonctionnel`

## Inputs

- dossier projet dans `02_PROSPECTS`
- fichiers du dossier `00_Entrées client`
- CRs du dossier `03_Comptes rendus` si présents
- version existante du cadrage fonctionnel si itération

## Processus

### 1. Contexte et périmètre strict

- identifier le dossier projet courant
- lire uniquement les fichiers de ce projet
- ignorer les fichiers d’autres projets
- utiliser les décisions déjà validées comme point de départ

### 2. Analyse du besoin

La skill doit reformuler :
- la compréhension du besoin
- la boucle de valeur
- les partis-pris structurants
- les thèmes à cadrer
- les parcours utilisateurs
- la démo si elle existe

### 3. Génération du document

- créer la structure de données interne (`analysis.json`)
- générer le document au format `.docx`
- contrôler la doc avant dépôt dans Drive

### 4. Dépôt

- déposer le document dans `01_Cadrage fonctionnel`
- nommer selon la convention du projet
- proposer remplacement/versionnement s’il existe déjà

## Livrables

- document de cadrage fonctionnel
- synthèse des choix métier et des points à valider

## Sorties utiles vers les autres workflows

- `av-parcours-miro` prend le cadrage fonctionnel comme matière première
- `av-presentation-client` s’appuie sur le cadrage fonctionnel pour la vision, le périmètre, les personas, le MVP et le parcours
- `av-devis` utilise les hypothèses de périmètre et la charge fonctionnelle pour estimer les jours
- `av-devis-tma` s’appuie aussi sur le cadrage fonctionnel pour la volumétrie et la maintenance

## Garde-fous

- ne pas inventer de contenu
- ne pas réécrire une décision déjà validée sans preuve
- signaler les zones incomplètes par `[à compléter]` ou `à valider`
- garder la voix à la première personne décrite dans la skill

## Etapes suivantes

- lancer le user story mapping sur Miro
- lancer le cadrage plateforme
- préparer le devis
- préparer la présentation client

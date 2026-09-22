# Workflow : avant-vente complet

## Objectif

Mettre en place un projet prospect dans l’arborescence standard, produire les cadrages, construire les parcours, chiffrer le projet, puis préparer la présentation client, tout en conservant la possibilité d’ajouter des comptes rendus de réunion au fil de l’avancement.

## Périmètre

Ce workflow couvre l’embarquement et la préparation d’un projet avant signature. Il s’appuie sur les skills existants du dépôt et respecte leur logique métier.

## Entrées

- nom du projet / prospect
- documents client et cahier des charges
- éventuelles décisions techniques déjà prises
- éventuels comptes rendus antérieurs

## Étapes

### 1. Initialisation du projet

Skill : `av-init-projet`

But :
- créer le dossier racine dans `02_PROSPECTS`
- créer les sous-dossiers standards
- copier les documents de base du projet
- préparer le terrain pour les cadrages

Livrables :
- dossier projet créé
- sous-dossiers `00_Entrées client`, `01_Cadrage fonctionnel`, `02_Cadrage plateforme`, `03_Comptes rendus`, `04_Devis`, `05_Présentation client`, `06_Démo`

### 2. Cadrage fonctionnel

Skill : `av-cadrage-fonctionnel`

But :
- analyser le besoin métier
- formaliser la compréhension du projet
- produire la boucle de valeur, les partis-pris, les thèmes, les parcours et la démo

Livrables :
- document de cadrage fonctionnel dans le dossier du projet

Dépendances :
- données client
- CR précédents si existants
- dossier projet créé

### 3. Cadrage technique de la plateforme

Skill : `av-cadrage-plateforme`

But :
- trancher les décisions structurantes (headless, couplé, multi-tenant, hébergement, etc.)
- documenter composants, serveurs, services tiers, budget et flux

Livrables :
- document de cadrage plateforme dans le dossier du projet

Dépendances :
- documents techniques du projet
- cadrage fonctionnel comme contexte de cohérence

### 4. Schémas d’architecture (parallèle aux cadrages)

Skills :
- `av-schema-logique`
- `av-schema-physique`

But :
- produire les schémas utiles à la présentation et à la validation technique

Livrables :
- schéma logique `.excalidraw`
- schéma physique `.excalidraw`

Note : l’insertion dans le document de cadrage plateforme reste manuelle selon les règles de la skill.

### 5. Parcours utilisateurs sur Miro

Skill : `av-parcours-miro`

But :
- traduire le cadrage fonctionnel en user story mapping
- créer la carte de parcours et la rendre exploitable dans la présentation

Livrables :
- URL du board Miro
- lien à copier dans le document de cadrage fonctionnel

Dépendances :
- cadrage fonctionnel
- personas et boucle de valeur

### 6. Chiffrage du projet

Skills :
- `av-devis`
- `av-devis-tma`

But :
- produire le devis forfaitaire du projet
- produire la TMA si le client en a besoin

Livrables :
- devis projet dans `04_Devis`
- devis TMA dans `04_Devis` si applicable

Dépendances :
- cadrage fonctionnel
- cadrage plateforme
- services tiers, charges, architecture, roadmap

### 7. Présentation client

Skill : `av-presentation-client`

But :
- synthétiser les livrables précédents
- préparer le deck de proposition client

Livrables :
- présentation client dans `05_Présentation client`

Dépendances :
- cadrage fonctionnel
- cadrage plateforme
- devis
- TMA
- Miro
- démo

### 8. Comptes rendus transverses

Skill : `av-compte-rendu-reunion`

But :
- documenter les réunions de cadrage, validation, revue ou décision
- consolider les décisions et actions en cours

Livrables :
- CR dans `03_Comptes rendus`

Rôle : transverse, sans dépendance de séquencement stricte.

## Sortie souhaitée

Un projet avant-vente est considéré prêt pour validation client lorsqu’il contient :

- dossier projet créé
- cadrage fonctionnel
- cadrage plateforme
- schémas logique et physique
- parcours Miro
- devis
- TMA si de besoin
- deck client
- CRs de suivi

## Règles de gouvernance

- Une sortie ne doit pas être inventée ou supposée lorsqu’un livrable n’existe pas.
- Les données de chiffrage doivent rester cohérentes avec les cadrages.
- Les CR sont transverses et peuvent intervenir en cours de route sans changer la logique du workflow.
- Le workflow s’arrête au niveau de la préparation client ; il n’inclut pas la livraison de projet en tant que telle.

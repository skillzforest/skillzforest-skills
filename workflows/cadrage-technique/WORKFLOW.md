# Workflow : cadrage technique / plateforme

## Objectif

Produire la note de cadrage technique de la plateforme, définir les décisions structurantes et préparer les éléments nécessaires au chiffrage et à la présentation.

## Skill principale

- `av-cadrage-plateforme`

## Inputs

- dossier projet
- documents techniques, architecture cible et décisions de conception
- cadrage fonctionnel déjà produit comme contexte métier
- éventuels CRs et décisions de réunion

## Processus

### 1. Analyse des décisions actées

- se baser sur les documents du projet
- ne pas réarbitrer une décision déjà choisie
- formuler la recommandation unique dans les cas incertains

### 2. Génération de la note

- recueillir : composants, flux, serveurs, services tiers, coûts indicatifs
- produire le document avec la charte de cadrage plateforme
- vérifier la cohérence avec le fonctionnel

### 3. Schémas d’architecture

Les schémas sont produits en complément et non en remplacement de la note de cadrage :

- `av-schema-logique`
- `av-schema-physique`

Les images doivent être exportées depuis Excalidraw et insérées manuellement dans la note de cadrage plateforme.

### 4. Dépôt dans Drive

- déposer la note dans `02_Cadrage plateforme`
- garder les schémas dans `Schémas d'architecture`

## Livrables

- document de cadrage technique
- schéma logique
- schéma physique

## Sorties utiles vers les autres workflows

- `av-devis` s’appuie sur les coûts serveurs, services tiers, licences et charges de développement
- `av-devis-tma` s’appuie sur l’exploitation, la criticité et la complexité de la plateforme
- `av-presentation-client` utilise la plateforme pour les sections architecture, budget et risques

## Garde-fous

- aucun chiffre inventé ; valeur manquante = placeholder
- ne pas réécrire les décisions déjà formalisées par ailleurs
- garder la logique “headless / couplé / multi-tenant” cohérente avec les données du projet
- le cadrage technique ne doit pas masquer les incertitudes ; elles sont explicites

## Etapes suivantes

- lancer le devis
- compléter la présentation client
- documenter les réunions de validation via `av-compte-rendu-reunion`

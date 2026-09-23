# Workflow : chiffrage / devis

## Objectif

Construire le devis du projet sur la base des cadrages fonctionnel et technique, puis ajouter la TMA si nécessaire.

## Skills principales

- `presales-quote`
- `presales-maintenance-quote`

## Inputs

- document de cadrage fonctionnel
- document de cadrage plateforme
- architecture cible et services tiers
- hypothèses de périmètre, volume et durée
- CRs avec éventuelles décisions de budget

## Processus

### 1. Préparer le cas de chiffrage

- identifier les lots à inclure
- comparer la charge fonctionnelle et technique
- recenser les services tiers et les coûts d’infrastructure

### 2. Devis projet (forfait)

- copier le master du devis dans le dossier projet
- remplir uniquement les champs d’entrée
- laisser les formules calculées intactes
- présenter le devis pour validation utilisateur

### 3. Devis TMA

- si le besoin de maintenance est prévu, produire le devis TMA séparé
- définir les jours/mois par type de maintenance
- signaler les hypothèses comme “à valider” si nécessaire

### 4. Validation

- vérifier la cohérence entre fonctionnel et plateforme
- vérifier que les inclusions et les montants sont conformes au cadrage
- retirer la note interne avant envoi client

## Livrables

- devis projet
- devis TMA si applicable

## Sorties utiles vers les autres workflows

- `presales-client-presentation` utilise les devis pour les sections budget et maintenance
- les décisions de pricing et de TMA doivent rester cohérentes avec le cadrage de la plateforme

## Garde-fous

- ne pas inventer des jours ou des coûts
- ne pas écraser les formules calculées
- ne pas présenter un devis sans validation préalable
- se limiter aux charges et services réellement identifiés dans les cadrages

## Etapes suivantes

- lancer le deck client
- consolider les éléments de présentation
- documenter les validations de budget par CR si besoin

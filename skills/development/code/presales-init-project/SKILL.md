---
name: presales-init-project
description: >-
  Initialise l'espace Google Drive d'un nouveau projet AVANT-VENTE : arborescence standardisée sous 02_PROSPECTS + copie automatique des documents modèles (cadrage fonctionnel, cadrage plateforme, compte rendu). Point de départ de toute la chaîne avant-vente (cadrages, CR, devis, présentation, démo) et socle de l'embarquement d'un prospect en ~20 min. Déclenche systématiquement ce skill dès que l'utilisateur veut démarrer, initialiser, créer ou préparer un nouveau projet, prospect ou client en avant-vente — « initialise le projet X », « nouveau projet avant-vente X », « prépare l'avant-vente de X », « on démarre le prospect X », « crée l'arborescence Drive pour X » — même sans le mot « Drive ». Suite Avant-Vente SkillzForest (préfixe presales-) ; les phases ultérieures du même projet (après-vente, delivery) ont un préfixe distinct, donc préciser « avant-vente » en cas de doute.
---

# presales-init-project — Initialisation Drive d'un projet avant-vente

Crée l'arborescence standard d'un projet **avant-vente** dans Google Drive et y dépose les documents modèles, pour qu'un nouveau prospect soit prêt à cadrer en quelques minutes (objectif d'embarquement ~20 min). Premier maillon de la suite **Avant-Vente SkillzForest**.

## Entrées

- **Nom du projet** (obligatoire) : nom court du prospect / projet (ex. « Brasserie Wicke », « SaaS QR »). Si absent, le demander avant toute action.
- **Nom du prospect / client** (optionnel) : si distinct du nom de projet, à noter pour information ; n'affecte pas l'arborescence.

Normaliser le nom pour les fichiers : conserver les accents et espaces dans les **titres Drive** (lisibilité), mais éviter les caractères interdits (`/ \ : * ? " < > |`).

## Emplacement et manifeste

**Dossier parent** (où sont créés les projets) — `02_PROSPECTS` :
`1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q`

**Masters à copier (voie A)** — copier ces Google Docs, ne jamais les modifier ni les déplacer :

| Master | fileId | Sous-dossier destination | Titre de la copie |
|---|---|---|---|
| Cadrage fonctionnel | `1ObFyncl2NF7EUlSKzu_u2GoIq2NBA9hC` | `01_Cadrage fonctionnel` | `Cadrage_fonctionnel_{Projet}` |
| Cadrage plateforme | `1TyEAnOwTkf8zYupvRjASpG94gA-GAw5f` | `02_Cadrage plateforme` | `Cadrage_plateforme_{Projet}` |
| Compte rendu | `11iiKyj98DH7k5JKywuXKZYwNTwbXY8Os` | `03_Comptes rendus` | `Compte_rendu_reunion_{Projet}` |

> Le master **Compte rendu** est copié une fois à l'init comme CR de base du projet. Le skill `presales-meeting-notes` crée ensuite un CR par réunion (nommé avec la date) dans le même dossier — pas de collision. Les masters **Devis** et **Présentation client** seront ajoutés à ce manifeste quand ils existeront (copie dans `04_Devis` et `05_Présentation client`).

## Arborescence à créer

```
{Projet}/
├── 00_Entrées client/
├── 01_Cadrage fonctionnel/        ← copie du master fonctionnel
├── 02_Cadrage plateforme/         ← copie du master plateforme
│   └── Schémas d'architecture/
├── 03_Comptes rendus/            ← copie du master CR (CR de base)
├── 04_Devis/
├── 05_Présentation client/
└── 06_Démo/
```

`06_Démo` ne stocke pas la démo (elle vit sur GitHub Pages) mais servira à consigner l'URL du dépôt et l'URL publique.

## Procédure

Les écritures Drive passent par l'approbation de l'utilisateur : les annoncer clairement et procéder étape par étape.

1. **Confirmer le plan.** Récapituler à l'utilisateur : nom du projet retenu, dossier parent, arborescence, masters qui seront copiés. Attendre son accord avant de créer quoi que ce soit.
2. **Vérifier l'existence.** Chercher si un dossier de même nom existe déjà sous le parent (`search_files` : `title contains '{Projet}'` filtré sur `mimeType = 'application/vnd.google-apps.folder'` et le bon parent). S'il existe, ne pas dupliquer : demander à l'utilisateur s'il faut réutiliser ou renommer.
3. **Créer le dossier racine** `{Projet}` sous le parent : `create_file` avec `mimeType = 'application/vnd.google-apps.folder'`, `parentId` = parent, `title` = `{Projet}`. Récupérer son `id`.
4. **Créer les sous-dossiers** dans l'ordre listé, chacun avec `parentId` = id de la racine. Puis créer `Schémas d'architecture` avec `parentId` = id de `02_Cadrage plateforme`.
5. **Copier les masters.** Pour chaque ligne du manifeste : `copy_file` du `fileId` master vers le sous-dossier destination (`parentId` = id du sous-dossier), avec le titre `{...}_{Projet}`. La copie reste un Google Doc propre ; ne jamais toucher au master source.
6. **Restituer.** Afficher l'arbre créé avec les liens (dossier racine + copies), et signaler tout élément déjà existant réutilisé.

## Règles

- **Validation avant exécution** : toujours présenter le plan et obtenir l'accord avant de créer.
- **Jamais de suppression** : ce skill ne supprime ni ne déplace rien. En cas de doublon, demander à l'utilisateur.
- **Masters intouchables** : on copie, on ne modifie jamais le master source. Les copies sont propres à chaque projet.
- **Idempotence** : re-lancer sur un projet existant ne doit pas créer de doublons silencieux ; vérifier d'abord.
- **Manifeste évolutif** : ajouter Devis et Présentation au manifeste dès que leurs masters existent, sans changer la logique.

## Sortie attendue

Un récapitulatif clair :

```
Projet « {Projet} » initialisé sous 02_PROSPECTS.
- Racine : {lien}
- 01_Cadrage fonctionnel/ → Cadrage_fonctionnel_{Projet} {lien}
- 02_Cadrage plateforme/  → Cadrage_plateforme_{Projet} {lien}
  └ Schémas d'architecture/
- 03_Comptes rendus/      → Compte_rendu_reunion_{Projet} {lien}
- 00_Entrées client/, 04_Devis/, 05_Présentation client/, 06_Démo/ créés (vides).
```

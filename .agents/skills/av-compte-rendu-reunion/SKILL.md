---
name: av-compte-rendu-reunion
description: >-
  Rédige un compte rendu de réunion professionnel à la charte (Google Doc) à partir d'un court interview. Le skill interroge l'utilisateur sur les éléments clés — date, durée, participants, canal, objet, sujets abordés, décisions prises, actions (avec responsable, échéance, statut), points en suspens, prochaine réunion — puis génère le CR rempli et le dépose dans le dossier 03_Comptes rendus du projet. Déclenche systématiquement ce skill dès que l'utilisateur veut un compte rendu, un CR, un relevé de décisions ou un suivi d'actions de réunion — « fais le CR de la réunion X », « compte rendu du call avec X », « note les décisions et actions de la réunion », « relevé de décisions » — même sans le mot « compte rendu ». Fait partie de la suite Avant-Vente AI Factory (préfixe av-).
compatibility: Nécessite l'exécution de code (Node.js) avec le paquet `docx`, et le connecteur Google Drive pour le dépôt.
---

# av-compte-rendu-reunion — Compte rendu de réunion

Produit un compte rendu de réunion rempli, à la charte, prêt à partager. Deux temps : **interroger** l'utilisateur sur le contenu de la réunion, puis **générer** le document et le **déposer** dans le projet.

## Règle absolue

**Ne jamais inventer de contenu.** Tout élément que l'utilisateur ne fournit pas est laissé en `[à compléter]` (le moteur s'en charge). Ne pas déduire de décisions ou d'actions non énoncées.

## Étape 1 — Interview

Recueillir les informations ci-dessous. Poser les questions groupées et de façon fluide (pas un formulaire aride) ; accepter « aucun / rien à signaler » pour les sections vides. Si le contexte de la conversation contient déjà certains éléments (réunion qui vient d'avoir lieu, notes collées), les extraire d'abord et ne demander que les manques.

1. **Projet** — nom du projet/prospect (sert à retrouver le dossier de dépôt).
2. **Cadre du call** — date, durée, canal (visio / téléphone / présentiel), objet du call.
3. **Participants** — liste (nom + rôle si connu).
4. **Sujets abordés** — l'ordre du jour réel, en quelques points.
5. **Décisions prises** — une ligne par décision actée.
6. **Actions à mener** — pour chacune : l'action, le responsable, l'échéance, le statut (À faire / En cours / Fait / Bloqué / Reporté ; défaut « À faire »), et une note éventuelle.
7. **Points en suspens** — questions ouvertes / arbitrages en attente (ou « aucun »).
8. **Prochaine réunion** — date, objet, préparation attendue.

Avant de générer, **récapituler brièvement** ce qui a été saisi pour validation (surtout décisions et actions).

## Étape 2 — Génération

1. Écrire les réponses dans un fichier `answers.json` (voir schéma ci-dessous).
2. Générer le document :
   ```bash
   node scripts/build_cr.js <answers.json> <sortie.docx>
   ```
   Le moteur applique la charte (Calibri, indigo/lavande, tableaux DXA, pied confidentiel) et gère un nombre variable de sujets, décisions et actions.
3. Contrôler visuellement si possible (conversion PDF + rasterisation) avant dépôt.

**Schéma `answers.json`** (tout champ est optionnel ; absent ⇒ `[à compléter]`) :
```json
{
  "projet": "…", "objetCall": "…", "date": "JJ/MM/AAAA", "duree": "…",
  "participants": "…", "canal": "…", "version": "1.0",
  "sujets": ["…", "…"],
  "decisions": ["…", "…"],
  "actions": [{"action":"…","responsable":"…","echeance":"JJ/MM","statut":"À faire","notes":"…"}],
  "suspens": ["…"],
  "prochaine": {"date":"…","objet":"…","preparation":"…"}
}
```

## Étape 3 — Dépôt dans Drive

1. Retrouver le dossier du projet sous `02_PROSPECTS` (parent `1sHtCH3Q9BHuAYq19bTdyau5IH5Cnmj5q`) via `search_files` (`title contains '{Projet}'`, `mimeType = 'application/vnd.google-apps.folder'`), puis son sous-dossier `03_Comptes rendus`.
2. Téléverser le `.docx` **avec conversion** en Google Doc dans ce dossier : `create_file` avec le contenu docx (base64), `contentMimeType` du docx, `parentId` = id de `03_Comptes rendus`, **sans** désactiver la conversion. Le CR devient un Google Doc propre.
3. **Nom du fichier** : `Compte_rendu_{Projet}_{AAAA-MM-JJ}` (convertir la date de réunion au format `AAAA-MM-JJ`). Ce nommage évite toute collision avec le CR de base déposé à l'init.
4. Restituer le lien du CR créé.

Si le projet n'existe pas encore dans Drive, proposer d'abord `av-init-projet`, ou livrer le `.docx` directement à l'utilisateur.

## Garde-fous

- **Validation avant dépôt** : récapituler décisions/actions et confirmer avant de générer/téléverser.
- **Aucune invention** : champs manquants ⇒ `[à compléter]`.
- **Le master CR n'est jamais modifié** : ce skill génère un nouveau document ; il ne touche pas au gabarit.
- **Réutilisable multi-client** : l'entête est signée « Arnaud BRETON » ; les participants figurent dans le tableau, pas dans la signature.

# AI Factory

Suite de skills Cursor pour automatiser les workflows d'avant-vente, delivery et opérations internes.

## Avant-vente (`av-`)

Skills dédiés à l'embarquement et au suivi des prospects avant signature.

| Skill | Fichier | Rôle |
|---|---|---|
| `av-init-projet` | `av-init-projet.skill` | Initialise l'arborescence Google Drive d'un nouveau projet sous `02_PROSPECTS` et copie les documents modèles (cadrage fonctionnel, cadrage plateforme, compte rendu). |
| `av-compte-rendu-reunion` | `av-compte-rendu-reunion.skill` | Rédige un compte rendu de réunion à la charte et le dépose dans le dossier `03_Comptes rendus` du projet. |

### Chaîne avant-vente

```
av-init-projet → cadrages → av-compte-rendu-reunion → devis → présentation → démo
```

Objectif : embarquer un nouveau prospect en ~20 minutes.

## Installation

1. Cloner ce dépôt.
2. Importer les fichiers `.skill` dans Cursor (Settings → Rules / Skills, ou glisser-déposer selon votre version).
3. Configurer les connecteurs requis (Google Drive pour les skills `av-`).

## Structure

```
ai-factory/
├── README.md
├── .gitignore
├── av-init-projet.skill
└── av-compte-rendu-reunion.skill
```

## Conventions

- Préfixe **av-** : avant-vente
- Préfixe **dv-** (à venir) : delivery / après-vente
- Les masters Google Drive ne sont jamais modifiés — chaque projet reçoit ses propres copies.

## Remote

```
https://github.com/arnoweb/ai-factory.git
```

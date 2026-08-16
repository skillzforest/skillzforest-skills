# AI Factory

## Plugin IA — AI Factory AV Suite

Un "plugin" est un bundle de skills (dossiers `av-*`) et d'un manifeste `plugin.json`. Ce dépôt fournit un plugin nommé **AI Factory AV Suite** contenant plusieurs skills Avant-Vente (devis, cadrage, compte-rendu, présentation, schémas).

### Installation (utilisateur)

1. Depuis la page des Releases GitHub, téléchargez le fichier `ai-factory-av-<version>.zip`.
2. Sur votre machine, exécutez :

```bash
# depuis la racine du repo (ou depuis n'importe où si vous avez le zip)
./scripts/install_plugin.sh path/to/ai-factory-av-<version>.zip
```

Le script installe le plugin sous `.agents/plugins/<id>` et crée des liens symboliques vers `.agents/skills/av-*`.

Alternativement vous pouvez :

```bash
unzip ai-factory-av-<version>.zip -d .agents/plugins/ai-factory-av
for d in .agents/plugins/ai-factory-av/av-*; do ln -sfn "$PWD/$d" ".agents/skills/$(basename $d)"; done
```

### Utilisation

- Invocation en conversation (UX skill-first) : invoquez naturellement la compétence (ex. « fais le devis de X ») ; le runtime lit `SKILL.md` et exécute la skill.
- Exécution locale / dev : utilisez les scripts fournis (ex. `scripts/fill_master.js`) pour exécuter une skill localement :

```bash
node scripts/fill_master.js --skill av-devis --master .agents/skills/av-devis/masters/Devis_Modulaire_MASTER.xlsx --data .agents/skills/av-devis/sample_input.json --name test --out .agents/skills/av-devis/out
```

### Publication / CI

Un workflow GitHub Action (`.github/workflows/build_plugin.yml`) construit automatiquement le zip et crée une Release avec l'archive jointe à chaque push sur `main`.


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

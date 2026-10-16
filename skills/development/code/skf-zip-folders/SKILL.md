---
name: skf-zip-folders
description: >-
  Demande le répertoire à traiter puis zippe chacun de ses sous-répertoires
  dans sa propre archive (nom-du-dossier.zip, posée à côté par défaut), sans les
  fichiers parasites (.DS_Store, .git, node_modules, __pycache__), vérifie
  chaque archive et fait le bilan. À utiliser dès que l'utilisateur veut
  zipper, compresser ou archiver tous les dossiers d'un répertoire, préparer
  un zip par skill, par projet ou par livrable, ou lance /skf-zip-folders.
argument-hint: "[répertoire] [--out <dossier>] [--overwrite] [--include-all]"
allowed-tools: Read, Bash(python3:*), Bash(python:*), Bash(py:*), Bash(command:*), Bash(ls:*)
---

# Zip Folders

Objectif : un zip par sous-répertoire d'un répertoire donné, en une seule
commande, sans rien abîmer.

Arguments reçus : `$ARGUMENTS`

Dossier de cette skill noté `$K` (utiliser le chemin réel) ; le script est
`$K/scripts/zip_folders.py` (Python 3.8 ou plus, bibliothèque standard,
aucun paquet à installer).

## 0. Trouver Python 3.8+

Avant toute chose, trouver un interpréteur utilisable, dans cet ordre :
`python3`, `python`, puis sous Windows `py -3`. Pour chacun :

```bash
python3 -c "import sys; print(sys.version.split()[0]); sys.exit(sys.version_info < (3, 8))"
```

Le premier qui répond avec un code de sortie 0 est noté `$PY` et sert pour
toutes les commandes suivantes. Sinon, selon le cas :

| Constat | Ce qu'on dit et propose |
|---|---|
| Aucune commande Python trouvée | « Python 3 n'est pas installé : il faut Python 3.8 ou plus pour cette skill. » Proposer de l'installer. |
| Seulement Python 2 (`python` répond 2.x) | « Seul Python 2 est installé : il est trop ancien et n'est plus maintenu. » Proposer d'installer Python 3 **à côté**. |
| Python 3.0 à 3.7 | « Python X.Y est installé, il faut 3.8 ou plus. » Proposer une montée de version. |

Installer ou mettre à jour **uniquement avec l'accord explicite** de
l'utilisateur, avec le gestionnaire de paquets déjà présent sur la machine :

| Système | Commande |
|---|---|
| macOS (Homebrew présent) | `brew install python` (ou `brew upgrade python`) |
| macOS sans Homebrew | `xcode-select --install` (fournit `python3`), ou l'installeur officiel de python.org |
| Debian / Ubuntu | `apt update && apt install -y python3` (droits administrateur) |
| Fedora / RHEL | `dnf install -y python3` (droits administrateur) |
| Arch | `pacman -S python` (droits administrateur) |
| Windows | `winget install -e --id Python.Python.3.12`, ou l'installeur de python.org (cocher « Add python.exe to PATH ») |

Règles :
- Ne jamais désinstaller, remplacer ou réassigner Python 2, ni modifier
  `/usr/bin/python` : d'autres outils peuvent en dépendre. Python 3 s'installe
  à côté.
- Les commandes Linux marquées « droits administrateur » se lancent
  précédées de `sudo`, qui demande le mot de passe de l'utilisateur : les lui
  laisser taper dans son terminal (préfixe `!` dans Claude Code) plutôt que
  de les lancer soi-même.
- Après l'installation, refaire la vérification ci-dessus (nouveau terminal
  si la commande reste introuvable) et ne continuer qu'une fois `$PY` trouvé.

**L'utilisateur refuse d'installer Python** : proposer de zipper quand même
avec les outils du système, dossier par dossier, depuis le répertoire à
traiter, avec les mêmes exclusions et sans écraser un zip existant :

```bash
# macOS / Linux (commande `zip` ; -y garde les liens symboliques comme liens)
for d in */; do d="${d%/}"; [ -e "$d.zip" ] && continue
  zip -rqy "$d.zip" "$d" -x '*/.DS_Store' '*/.git/*' '*/node_modules/*' '*/__pycache__/*' '*/__MACOSX/*'
done
```

```powershell
# Windows (PowerShell) : Compress-Archive ne sait pas exclure, signaler
# que .git / node_modules seront inclus s'ils existent
Get-ChildItem -Directory | Where-Object { -not (Test-Path "$($_.Name).zip") } |
  ForEach-Object { Compress-Archive -Path $_.FullName -DestinationPath "$($_.Name).zip" }
```

Dans ce mode, pas de vérification d'archive ni de rapport JSON : contrôler
avec `unzip -l` (ou `ls`) et faire le bilan à la main. Si `zip` est absent
lui aussi, le dire et s'arrêter.

## 1. Demander le répertoire

Si `$ARGUMENTS` ne donne pas de répertoire, **demander son nom** (ou son
chemin) en une phrase : « Quel répertoire dois-je traiter ? Je zipperai
chacun de ses sous-répertoires. » Un nom seul se cherche d'abord dans le
répertoire courant ; s'il est introuvable ou ambigu, demander le chemin
plutôt que deviner. Ne jamais partir du répertoire courant sans accord.

## 2. Montrer ce qui va être fait

```bash
$PY "$K/scripts/zip_folders.py" "<répertoire>" --dry-run [--out <dossier>]
```

Annoncer en quelques lignes : le répertoire, les sous-répertoires qui seront
zippés, où iront les archives (à côté des dossiers par défaut, ou `--out`),
les zips **déjà présents** (`existing`) et les dossiers **vides** (`empty`).

- Aucun sous-répertoire : le dire et s'arrêter.
- Des zips existent déjà : demander s'il faut les remplacer (`--overwrite`)
  ou les laisser tels quels — par défaut ils ne sont pas touchés.
- Plus de 20 dossiers, ou un dossier visiblement énorme (`ls`) : confirmer
  avant de lancer.

Sinon, enchaîner sans redemander.

## 3. Zipper

```bash
$PY "$K/scripts/zip_folders.py" "<répertoire>" [--out <dossier>] [--overwrite] [--include-all]
```

Ce que fait le script :
- une archive `<nom>.zip` par sous-répertoire direct, dont la racine est le
  dossier `<nom>/` (comme « Compresser » du Finder) ;
- ignore les sous-répertoires cachés (`.git`, `.venv`…) et, dans chaque
  dossier, `.DS_Store`, `__MACOSX`, `.git`, `node_modules`, `__pycache__`,
  `Thumbs.db` — sauf `--include-all` (seulement si l'utilisateur le demande) ;
- ne suit pas les liens symboliques qui sortent du dossier ;
- écrit dans un fichier temporaire, vérifie l'archive, puis la met en place :
  une archive ratée ne remplace jamais une archive existante ;
- continue avec les autres dossiers si l'un échoue (`errors`).

Ne jamais supprimer ni déplacer les dossiers d'origine.

## 4. Rendre compte

Un tableau court, une ligne par archive : dossier, archive, nombre de
fichiers, taille. Puis, s'il y en a : les zips laissés tels quels, les
dossiers vides (zippés quand même, signalés), les erreurs avec leur cause.
Terminer par le chemin où se trouvent les archives.

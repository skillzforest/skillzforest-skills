# Récupérer des fichiers dans le cloud

Ordre d'essai : du plus simple (déjà sur le disque) au plus lourd. Toujours **lister
d'abord, choisir ensuite** : on ne télécharge jamais un drive entier. Au-delà de
30 fichiers ou de 1 Go, montrer la liste et demander lesquels prendre.

Tout ce qui est téléchargé atterrit dans `shorts/<slug>/inbox/<origine>/`, puis passe par
`collect_media.py --origin <origine>` qui le range et l'inventorie.

## 1. Dossier synchronisé sur l'ordinateur (le plus fréquent)

Les applications Google Drive, OneDrive, SharePoint (via OneDrive), Dropbox et Box
montent les fichiers comme un dossier local :

| Système | Où chercher |
|---|---|
| macOS | `~/Library/CloudStorage/` (`GoogleDrive-<compte>/`, `OneDrive-<organisation>/`, `Dropbox/`, `Box-Box/`), anciens montages `~/Google Drive`, `~/Dropbox` |
| Windows | `%USERPROFILE%\OneDrive - <organisation>\`, `G:\` ou `%USERPROFILE%\Google Drive\`, `%USERPROFILE%\Dropbox\` |
| Linux | point de montage `rclone mount` ou `~/Dropbox` |

Une bibliothèque SharePoint apparaît dans OneDrive après « Ajouter un raccourci à Mes
fichiers » ou « Synchroniser » sur le site SharePoint. Les fichiers « en ligne
uniquement » se téléchargent à la première lecture : la copie peut être lente.

```bash
ls ~/Library/CloudStorage/ 2>/dev/null
python3 "$K/scripts/collect_media.py" ~/Library/CloudStorage/GoogleDrive-*/Mon\ Drive/Marketing/Shorts \
  --short shorts/<slug> --origin gdrive --licence own --dry-run
```

## 2. Connecteur de l'agent

Si l'environnement propose un connecteur (outils de recherche et de téléchargement de
fichiers Google Drive, Microsoft 365 / SharePoint / OneDrive, Dropbox, Box) :

1. Rechercher par nom de dossier ou mots-clés (« logo », « charte », « démo », « brand »).
2. Lister le contenu, montrer nom, type, taille, date.
3. Télécharger les fichiers retenus et les écrire dans `inbox/<origine>/` (un document
   Google — Docs, Slides — s'exporte en PDF ou en texte).

## 3. rclone (si l'utilisateur l'a configuré)

```bash
rclone listremotes                                    # ex. sharepoint:, gdrive:
rclone lsf "sharepoint:Marketing/Shorts" --max-depth 2
rclone copy "sharepoint:Marketing/Shorts" shorts/<slug>/inbox/sharepoint --max-size 300M --progress
```

Ne pas configurer un remote à la place de l'utilisateur (authentification interactive).

## 4. Lien de partage public

| Service | Lien direct |
|---|---|
| Google Drive (fichier) | `https://drive.google.com/uc?export=download&id=<ID>` — les gros fichiers demandent une confirmation : préférer le connecteur |
| Dropbox | remplacer `dl=0` par `dl=1` |
| OneDrive / SharePoint | ajouter `download=1` au lien de partage (`&download=1` ou `?download=1`) |
| WeTransfer, autres | ouvrir le lien dans le navigateur et demander le fichier |

```bash
curl -L --fail -o shorts/<slug>/inbox/url/demo.mp4 "<lien direct>"
```

Un lien de dossier (pas de fichier) ne se télécharge pas ainsi : demander un zip, ou
passer par l'option 1 ou 2.

## 5. Sinon

Demander à l'utilisateur de déposer les fichiers dans `shorts/<slug>/inbox/` et continuer.

---
name: "skf-optimiser-images-web"
description: "Optimise toutes les images d'un répertoire pour le web (WebP, AVIF, JPEG, PNG) avec ImageMagick, après avoir demandé le niveau de qualité, le format de sortie et s'il faut écraser les originaux ou créer un sous-répertoire."
---

# Optimiser les images d'un répertoire pour le web

Outil utilisé : **ImageMagick** (open source, licence Apache 2.0), disponible sur macOS, Windows et Linux. Il gère nativement JPEG, PNG, WebP et AVIF, le redimensionnement, la suppression des métadonnées et la correction d'orientation EXIF. ffmpeg sert uniquement de solution de secours pour l'AVIF si la version Linux d'ImageMagick ne le supporte pas.

Les commandes s'exécutent sur la machine qui contient le répertoire (shell local ou shell distant de l'ordinateur de l'utilisateur). Si aucun accès au répertoire n'est possible, demander à l'utilisateur de connecter le dossier.

## Règles

- La destination dépend du choix de l'utilisateur (étape 2) : **sous-répertoire** `web/` créé dans le répertoire source, ou **écrasement** des originaux. Sans réponse claire, choisir le sous-répertoire.
- L'écrasement est irréversible : le demander explicitement, puis le reconfirmer une fois avec le nombre d'images concernées avant de lancer.
- Ne jamais installer un logiciel sans l'accord explicite de l'utilisateur.
- Si un fichier optimisé est plus lourd que l'original **dans le même format**, garder l'original : en mode sous-répertoire, y copier l'original ; en mode écrasement, ne pas toucher au fichier.
- Les GIF animés et les SVG sont ignorés et listés dans le rapport.

## Étape 1 : identifier le répertoire

Si l'utilisateur n'a pas donné le chemin, le lui demander. Vérifier que le dossier existe et compter les images concernées (extensions : jpg, jpeg, png, webp, avif, tif, tiff, bmp, heic, insensible à la casse), en excluant un éventuel sous-dossier `web/` issu d'une exécution précédente. S'il n'y a aucune image, le dire et s'arrêter.

## Étape 2 : demander les paramètres

Poser les questions en une seule fois avec AskUserQuestion (ou en texte si l'outil est absent) :

1. **Format de sortie** : WebP (Recommandé) / AVIF (plus léger, encodage plus lent) / JPEG / Garder le format d'origine. PNG reste accessible via « Autre ».
2. **Niveau de qualité** : Équilibrée (Recommandé) / Haute / Compacte.
3. **Taille maximale (plus grand côté)** : 1920 px (Recommandé) / 2560 px / 1280 px / Ne pas redimensionner.
4. **Destination** : Créer un sous-répertoire `web/` (Recommandé, les originaux restent intacts) / Écraser les images d'origine.

Si l'utilisateur choisit l'écrasement avec un format différent de l'original (ex. JPEG vers WebP), préciser que les fichiers d'origine seront supprimés et remplacés par la nouvelle extension, et que les pages HTML, CSS ou CMS qui pointent vers les anciens noms devront être mises à jour.

Correspondance qualité :

| Niveau | WebP | AVIF | JPEG | PNG |
|---|---|---|---|---|
| Haute | 85 | 70 | 88 | sans perte, compression max |
| Équilibrée | 78 | 60 | 82 | sans perte, compression max |
| Compacte | 65 | 48 | 72 | réduction à 256 couleurs |

## Étape 3 : vérifier et installer ImageMagick

Détecter l'OS puis tester, dans l'ordre :
- `magick -version` (ImageMagick 7, tous OS)
- sous Linux uniquement : `convert -version` (ImageMagick 6). Sous Windows, ne jamais appeler `convert` : c'est une commande système de conversion de disque.

Retenir la commande trouvée dans `IM` (`magick` ou `convert`).

Si absent, proposer la commande d'installation adaptée et attendre l'accord :

| OS | Commande |
|---|---|
| macOS | `brew install imagemagick` (sans Homebrew : `sudo port install ImageMagick`) |
| Windows | `winget install ImageMagick.ImageMagick` (ou `choco install imagemagick`, `scoop install imagemagick`) puis ouvrir un nouveau terminal |
| Debian / Ubuntu | `sudo apt install imagemagick` |
| Fedora | `sudo dnf install ImageMagick` |
| Arch | `sudo pacman -S imagemagick` |

Après installation, relancer le test de version.

Vérifier ensuite que le format choisi est supporté : `$IM -list format` doit contenir `WEBP` ou `AVIF` avec le mode `rw`. Pour les sources HEIC, vérifier aussi `HEIC`.

Si l'AVIF manque (cas fréquent sur les anciennes distributions Linux), proposer au choix :
- passer en WebP ;
- utiliser ffmpeg (`sudo apt install ffmpeg`), avec la commande `ffmpeg -y -i <in> -vf "scale='min(MAX,iw)':'min(MAX,ih)':force_original_aspect_ratio=decrease" -c:v libaom-av1 -still-picture 1 -crf <CRF> <out>.avif` où CRF vaut 24 (Haute), 30 (Équilibrée), 38 (Compacte). Sans redimensionnement, retirer le `-vf`.

## Étape 4 : construire les options

Options communes : `-auto-orient -strip -colorspace sRGB`, plus `-resize "MAXxMAX>"` si un redimensionnement est demandé (le `>` évite d'agrandir les petites images).

Options par format (Q = valeur du tableau) :
- **WebP** : `-quality Q -define webp:method=6`
- **AVIF** : `-quality Q`
- **JPEG** : `-quality Q -sampling-factor 4:2:0 -interlace Plane -background white -alpha remove -alpha off` (le JPEG n'a pas de transparence : fond blanc)
- **PNG** : `-define png:compression-level=9 -define png:compression-filter=5`, plus `-colors 256` en qualité Compacte

En mode « Garder le format d'origine », appliquer les options correspondant à l'extension de chaque fichier (tif, bmp et heic sont convertis en JPEG).

`$opts` (PowerShell) est un tableau, par exemple `@('-auto-orient','-strip','-colorspace','sRGB','-resize','1920x1920>','-quality','78','-define','webp:method=6')`.

## Étape 5 : traiter le répertoire

Avant le traitement complet, tester sur une seule image et vérifier que le fichier produit s'ouvre (`$IM identify <fichier>`). En mode écrasement, faire ce test dans un fichier temporaire, sans toucher à l'original. Pour plus de 200 images, prévenir que l'AVIF peut prendre plusieurs minutes.

### Mode A : sous-répertoire `web/`

La sortie va dans `<répertoire>/web/`, qui reproduit l'arborescence. Le dossier `web/` est exclu du parcours pour ne pas retraiter ses propres fichiers.

**macOS / Linux (bash)**

```bash
SRC="/chemin/du/dossier"; SRC="${SRC%/}"; DST="$SRC/web"
find "$SRC" -path "$DST" -prune -o -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.avif' -o -iname '*.tif' -o -iname '*.tiff' -o -iname '*.bmp' -o -iname '*.heic' \) -print0 |
while IFS= read -r -d '' f; do
  rel="${f#$SRC/}"; out="$DST/${rel%.*}.$EXT"
  mkdir -p "$(dirname "$out")"
  $IM "$f" $OPTS "$out" || echo "ECHEC: $f"
done
```

**Windows (PowerShell)**

```powershell
$src = (Resolve-Path "C:\chemin\du\dossier").Path.TrimEnd('\'); $dst = Join-Path $src 'web'
Get-ChildItem $src -Recurse -File -Include *.jpg,*.jpeg,*.png,*.webp,*.avif,*.tif,*.tiff,*.bmp,*.heic |
  Where-Object { $_.FullName -notlike "$dst\*" } | ForEach-Object {
  $rel = $_.FullName.Substring($src.Length).TrimStart('\')
  $out = Join-Path $dst ([IO.Path]::ChangeExtension($rel, $ext))
  New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
  & magick $_.FullName @opts $out
  if ($LASTEXITCODE -ne 0) { Write-Output "ECHEC: $($_.FullName)" }
}
```

### Mode B : écrasement des originaux

Chaque image est d'abord encodée dans un fichier temporaire, puis remplace l'original seulement si l'encodage a réussi et que le fichier s'ouvre. Un échec laisse l'original intact.

- **Même extension** (ex. JPEG vers JPEG) : le fichier temporaire remplace directement l'original.
- **Extension différente** (ex. JPEG vers WebP) : le nouveau fichier est créé à côté, puis l'original est supprimé.

Avant l'écrasement, noter la taille de chaque original pour calculer le gain dans le rapport, et appliquer la règle « plus lourd dans le même format » : dans ce cas, supprimer le fichier temporaire et garder l'original.

Sur l'ordinateur de l'utilisateur via le shell distant, la suppression est bloquée par défaut : demander l'autorisation de suppression pour le dossier concerné. Si elle est refusée ou indisponible, déplacer les originaux dans un sous-dossier `_a_supprimer/` et le signaler dans le rapport.

**macOS / Linux (bash)**

```bash
SRC="/chemin/du/dossier"; SRC="${SRC%/}"
find "$SRC" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.avif' -o -iname '*.tif' -o -iname '*.tiff' -o -iname '*.bmp' -o -iname '*.heic' \) -print0 |
while IFS= read -r -d '' f; do
  out="${f%.*}.$EXT"; tmp="${f%.*}.tmp-opt.$EXT"
  if $IM "$f" $OPTS "$tmp" && $IM identify "$tmp" >/dev/null 2>&1; then
    mv -f "$tmp" "$out"
    [ "$f" != "$out" ] && rm -f "$f"
  else
    rm -f "$tmp"; echo "ECHEC: $f"
  fi
done
```

**Windows (PowerShell)**

```powershell
$src = (Resolve-Path "C:\chemin\du\dossier").Path.TrimEnd('\')
Get-ChildItem $src -Recurse -File -Include *.jpg,*.jpeg,*.png,*.webp,*.avif,*.tif,*.tiff,*.bmp,*.heic | ForEach-Object {
  $out = [IO.Path]::ChangeExtension($_.FullName, $ext)
  $tmp = [IO.Path]::ChangeExtension($_.FullName, "tmp-opt.$ext")
  & magick $_.FullName @opts $tmp
  if ($LASTEXITCODE -eq 0) {
    Move-Item -Force $tmp $out
    if ($_.FullName -ne $out) { Remove-Item $_.FullName }
  } else {
    Remove-Item $tmp -ErrorAction SilentlyContinue; Write-Output "ECHEC: $($_.FullName)"
  }
}
```

## Étape 6 : rapport

Calculer et présenter :
- nombre d'images traitées, ignorées, en échec ;
- poids total avant / après et gain en pourcentage ;
- les 5 plus gros gains ;
- la destination : chemin du sous-répertoire `web/`, ou mention « originaux remplacés » (avec le dossier `_a_supprimer/` s'il a été utilisé).

Terminer en une phrase : proposer de relancer avec un autre niveau de qualité si le rendu ne convient pas (en mode écrasement, rappeler que la relance partira des images déjà compressées).
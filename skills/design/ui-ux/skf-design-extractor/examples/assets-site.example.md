# Assets du site — tailles à produire

Toutes les images et vidéos à fournir pour le site, avec la taille à exporter.

**Méthode.** Chaque taille part de la plus grande largeur réellement affichée à
l'écran (toutes tailles d'écran confondues), exportée à environ ×2 pour les
écrans Retina — jamais au-delà, pour ne pas alourdir les pages.

## Règles communes

- **Format d'export : WebP, qualité 75–80** (JPEG accepté, PNG seulement si
  transparence nécessaire). Le SVG n'est pas accepté.
- **Limites du serveur :** 1 Mo par image, 50 Mo par vidéo. Les poids visés
  ci-dessous sont bien en dessous.
- **Pas de texte dans les images :** elles sont recadrées selon l'écran et le
  site est bilingue (FR/EN).
- **Sujet au centre**, avec environ 10 % de marge : les bords peuvent être
  coupés.

## Images

| # | Emplacement | Largeur affichée max | Format | Taille à produire | Poids visé |
|---|---|---|---|---|---|
| **Catégories** ||||||
| 1 | Home : carte « Explorer par besoin » | 220 px (desktop, 6 colonnes), 320 px (tablette) | 4:3 | **480 × 360** | ≤ 40 Ko |
| 2 | Page catégorie : bandeau (desktop uniquement) | 440 px | 4:3 | **880 × 660** | ≤ 90 Ko |
| 3 | Page catégorie : carte « Grand thème » (partie droite) | ≈ 200 × 180 px | ≈ 1:1 | **400 × 400** | ≤ 35 Ko |
| 4 | Page sous-catégorie : bandeau | 440 px | 4:3 | même image que la ligne 3 | — |
| **Skills et packs** ||||||
| 5 | Carte produit (home, pages catégorie) | 332 px (desktop), 480 px (tablette), 280 px (mobile) | affichée en 16:10, champ carré | **640 × 640** | ≤ 60 Ko |
| 6 | Même image, version mobile | 280 px | 1:1 | **400 × 400** | ≤ 30 Ko |
| 7 | Icône (listes, menu, en-tête de la page détail) | 36 à 96 px | 1:1 | images des lignes 5 et 6 | — |
| 8 | Page détail : visuel principal | ≈ 600 px | 16:9 | **1200 × 675** | ≤ 120 Ko |
| 9 | Page détail : couverture de la vidéo | ≈ 600 px | 16:9 | **1200 × 675** | ≤ 120 Ko |
| 10 | Page détail : cartes « Résultats » | ≈ 370 px | 2:1 | **800 × 400** | ≤ 60 Ko |
| **Articles (Actualités et Apprendre)** ||||||
| 11 | Image de l'article : à la une, cartes, en-tête, partage réseaux | ≈ 840 px (à la une) | 16:9 | **1280 × 720** | ≤ 130 Ko |
| **Pages spéciales** ||||||
| 12 | Home : visuel du haut | 576 px | 5:4 | **1152 × 920** | ≤ 150 Ko |
| 13 | Page Manager : image ou couverture de la vidéo | ≈ 580 px | 16:9 | **1200 × 675** | ≤ 120 Ko |

### Précisions

- **Lignes 1 et 2 :** la catégorie n'a aujourd'hui qu'un seul champ image, utilisé
  à la fois pour la carte de la home et pour le bandeau. En attendant un
  second champ, fournir l'image du bandeau (880 × 660).
- **Ligne 5 :** le champ est carré (il sert aussi d'icône), mais la carte
  l'affiche en 16:10. Le haut et le bas sont donc coupés (≈ 37 % de la
  hauteur). Garder le sujet dans la bande horizontale centrale.
- **Ligne 7 :** en Grand public, l'icône est rognée en rond.
- **Ligne 11 :** sur les petites cartes, l'image est recadrée en 4:3 (bords
  gauche et droit coupés). 1280 px de large couvre aussi l'aperçu de partage
  sur les réseaux sociaux (minimum 1200 px).

## Vidéos

| # | Emplacement | Format | Résolution | Durée / poids visé | Remarques |
|---|---|---|---|---|---|
| 14 | Home : vidéo du haut (en boucle, sans son) | 5:4 | **960 × 768** | 6 à 10 s, **≤ 2 Mo** | Lancée automatiquement : chaque visiteur la télécharge. Supprimer la piste audio. Prévoir une image d'attente (ligne 12). |
| 15 | Page détail : vidéo de démo | 16:9 | **1280 × 720** | ≤ 30 s, **≤ 5 Mo** (limite du back-office) | Rien n'est téléchargé avant le clic. Prévoir une couverture (ligne 9). |
| 16 | Page Manager : présentation | 16:9 | **1280 × 720** | ≤ 20 Mo | Avec le son et les commandes. Plus longue : passer par YouTube ou Vimeo. |
| 17 | Article (Apprendre) | 16:9 | 1280 × 720 | — | **YouTube ou Vimeo de préférence** : ils assurent la diffusion et la bande passante. |

### Réglages d'export vidéo

- MP4, codec **H.264** (WebM accepté)
- 24 à 30 images par seconde
- Débit environ **1 à 1,5 Mbit/s** en 720p
- Option **« fast start »** (web optimized) activée : la lecture démarre avant
  la fin du téléchargement

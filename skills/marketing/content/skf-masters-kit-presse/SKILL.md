---
name: skf-masters-kit-presse
description: >-
  Relève la charte graphique d'un site web (couleurs, polices, logos, ton) puis
  crée deux masters réutilisables pour présenter un produit digital à la presse,
  aux blogueurs et aux influenceurs : une présentation 16:9 (Google Slides ou
  .pptx) et un document (Google Docs ou .docx) réunissant communiqué de presse,
  fiche créateurs et questions-réponses. Plan standard de lancement, champs à
  remplir, aucun contenu produit inventé. À utiliser dès que l'utilisateur veut
  un kit presse, un dossier de presse, des gabarits de communiqué ou de
  présentation produit aux couleurs d'un site, ou lance /skf-masters-kit-presse.
argument-hint: "<url du site> [--slides google|pptx] [--document google|docx] [--langue fr|en|es] [--dossier <dossier Drive>]"
allowed-tools: Read, Write, Edit, WebFetch, Bash(python3:*), Bash(python:*), Bash(soffice:*), Bash(pdftoppm:*), Bash(ls:*), Bash(mkdir:*)
---

# skf-masters-kit-presse

Produit deux **masters** aux couleurs d'un site, à copier ensuite pour chaque campagne de lancement :

1. **Présentation presse** (16:9) : 17 slides au plan standard d'un lancement de produit digital.
2. **Document** : communiqué de presse (partie A), fiche créateurs pour blogueurs et influenceurs (partie B), questions-réponses (partie C).

Principe directeur : **la charte vient du site, le contenu viendra plus tard**. Les masters ne contiennent que des champs `{{CHAMP}}`, des consignes et des cadres de visuels. Aucune fonctionnalité, aucun chiffre, aucune couleur n'est inventé.

Arguments reçus : `$ARGUMENTS`

Les scripts sont dans `scripts/` du dossier de cette skill (noté `$S`), les plans dans `references/` (noté `$R`). Utiliser les chemins réels.

## 1. Entrées

| Entrée | Défaut |
|---|---|
| URL du site (obligatoire) | |
| Format des slides : `google` (Google Slides) ou `pptx` | `google` si un connecteur Google Drive est disponible, sinon `pptx` |
| Format du document : `google` (Google Docs) ou `docx` | même règle |
| Langue des masters : `fr`, `en`, `es` | `fr` |
| Dossier Drive de destination | `Masters kit presse - <Marque>` |

Demander en une seule question ce qui manque et ne peut pas être déduit. Si personne ne répond, prendre les défauts et les écrire en tête du compte rendu.

Prérequis : `python3 -m pip install python-pptx python-docx lxml` (si absents) ; LibreOffice (`soffice`) et `pdftoppm` pour la vérification visuelle.

## 2. Relever la charte

Sources, par ordre de priorité. S'arrêter dès que la charte est complète, compléter sinon avec les suivantes :

1. **Charte publiée** : tester `/brand/design-system.md`, `/brand`, `/press`, `/presse`, `/media-kit`, `/llms.txt`, et les liens « Presse », « Brand », « Kit média » du pied de page. Une charte écrite prime sur tout le reste.
2. **Styles calculés** dans un navigateur, si l'environnement en propose un (lire d'abord le skill de ce navigateur) : ouvrir l'accueil et une page produit, puis relever en JavaScript :
   - les variables CSS de `:root` (`getComputedStyle(document.documentElement)`), thème sombre compris ;
   - `font-family`, graisse et taille de `body`, `h1`, `h2`, boutons ;
   - fonds et couleurs de texte de `body`, en-tête, pied de page, bouton principal, liens.
3. **Repli sans navigateur** : WebFetch de la page et de ses feuilles de style, en demandant explicitement les variables CSS, les `@font-face`, les liens Google Fonts et les couleurs les plus fréquentes.
4. **Logos** : charte, page presse, logo de l'en-tête, `og:image`, `apple-touch-icon`. Noter l'URL absolue et le fond sur lequel chaque logo est lisible (sombre, clair, les deux).
5. **Ton** : titre principal, slogan, deux ou trois paragraphes. Noter tutoiement ou vouvoiement, longueur des phrases, vocabulaire, signature.

Écrire `brand-profile.json` sur le modèle de `examples/brand-profile.example.json`. Couleurs indispensables : `fond_sombre`, `fond_clair`, `texte`, `primaire` ; optionnelles : `texte_secondaire`, `secondaire`, `accent`, `bordure`, `texte_fonce`. `theme_site` vaut `sombre` ou `clair` selon le fond dominant du site.

Règles :
- **Ne jamais inventer** une couleur, une police ou un logo. Une valeur introuvable va dans `a_verifier`, avec la source consultée.
- Une police absente de Google Fonts ne s'affichera pas dans Google Slides ni Google Docs : retenir la police Google Fonts la plus proche et l'inscrire dans `a_verifier`.
- Si l'utilisateur est présent, lui montrer la palette relevée (aperçu visuel inline) avant de construire.

## 3. Valider la charte et dériver les palettes

```bash
python3 "$S/brand_check.py" brand-profile.json
```

Le script :
- refuse un profil sans les couleurs indispensables (code 2) : les relever ou les demander ;
- dérive la palette des **slides** (fond dominant du site) et la palette **fond clair** du document (fond blanc, couleurs vives assombries dans leur teinte jusqu'à 4,5:1 pour le texte et les titres, 3:1 pour les filets) ;
- écrit `palettes` et `contraste` dans le profil, ajoute chaque ajustement à `a_verifier`, et sort en erreur (code 1) si une paire reste sous le seuil.

Sur une erreur de contraste, corriger le profil avec une autre couleur du site, jamais avec une couleur nouvelle.

## 4. Choisir la langue

Les plans par défaut sont en français : `$R/plan-slides.fr.json` et `$R/plan-document.fr.json`. Pour une autre langue, traduire ces deux fichiers dans le dossier de travail (`plan-slides.en.json`…) en gardant **à l'identique** les noms de champs `{{...}}`, les clés JSON et les types de blocs ; seuls les textes changent. Adapter aussi le tutoiement ou vouvoiement relevé à l'étape 2.

Le plan peut être ajusté au produit (retirer une slide, ajouter une carte) en éditant la copie, jamais le fichier de référence.

## 5. Construire les masters

Récupérer d'abord les logos en fichiers locaux quand c'est possible (charte téléchargeable, fichiers fournis par l'utilisateur). Le shell d'un environnement en ligne ne peut souvent pas télécharger depuis un site quelconque : dans ce cas, construire sans logo (un cadre « Logo » est posé) et l'insérer par URL à l'étape 6.

```bash
python3 "$S/build_masters.py" brand-profile.json --out masters \
  [--logo logo-fond-sombre.png] [--logo-clair logo-fond-clair.png] \
  [--slides-plan plan-slides.<langue>.json] [--doc-plan plan-document.<langue>.json] \
  [--only slides|document]
```

Résultat :

```text
masters/
├── <Marque>_Presentation_presse_MASTER.pptx       # 16:9, thème couleurs et polices de la marque
├── <Marque>_Communique_fiche_createurs_MASTER.docx # A4, fond blanc, styles nommés
└── champs.json                                     # champs remplis par la charte et champs à remplir
```

`{{MARQUE}}` et `{{SITE}}` sont remplis depuis la charte ; tous les autres champs restent à remplir à chaque copie.

### Plan de la présentation

| # | Slide | Champs principaux |
|---|---|---|
| 0 | Mode d'emploi (à supprimer) | nombre de champs ; liste complète en notes |
| 1 | Couverture | `{{PRODUIT_NOM}}`, `{{PROMESSE}}`, `{{DATE_LANCEMENT}}`, logo |
| 2 | En une phrase | `{{PITCH_UNE_PHRASE}}` |
| 3 | Le constat | `{{PROBLEME_TITRE}}`, 3 constats |
| 4 | La solution | 3 points, visuel principal |
| 5 | Pour qui | 3 profils et leur besoin |
| 6 | Comment ça marche | 3 étapes |
| 7 | Fonctionnalités clés | 4 cartes titre + bénéfice |
| 8 | Zoom sur (à dupliquer) | une fonctionnalité, capture |
| 9 | En images | 3 captures légendées |
| 10 | Ce qui change | 3 différences vérifiables |
| 11 | Chiffres clés | 3 chiffres + légendes |
| 12 | Disponibilité | plateformes, prix, date, lien |
| 13 | Et ensuite | 3 éléments prévus |
| 14 | Le mot du fondateur | citation, porte-parole, photo |
| 15 | Ressources presse | kit, visuels HD, démo, accès test |
| 16 | Contact presse | coordonnées, logo |

Chaque slide porte sa consigne de remplissage dans les notes du présentateur ; chaque visuel attendu est un cadre pointillé nommé `Image : <visuel>`.

### Plan du document

- **A. Communiqué de presse** (une page, deux au maximum) : bandeau logo ; « COMMUNIQUÉ DE PRESSE · ville, date » ; titre ; chapeau ; le problème ; la solution et 3 fonctionnalités ; disponibilité et prix ; citation ; encadré chiffres clés ; à propos ; contact presse et lien du kit.
- **B. Fiche créateurs** : le produit en trois phrases ; messages clés et formulations à éviter ; tableau d'idées de contenus (angle, format, ce qu'on montre) ; à montrer, à éviter à l'écran ; liens, comptes, hashtags, lien suivi ; mentions obligatoires (partenariat signalé, fonctions d'IA présentées comme telles) ; contact créateurs.
- **C. Questions-réponses** : 7 questions types, réponses en champs.

Les consignes sont des paragraphes au style `Consigne` (gris, italique) à supprimer à l'usage.

## 6. Passer au format Google (si demandé)

1. Envoyer le .pptx et le .docx dans le dossier Drive cible avec le connecteur Google Drive, en demandant la conversion en Google Slides et Google Docs. Si la conversion n'est pas possible, livrer les fichiers Office et le dire en une ligne.
2. Logos absents : les insérer par leur URL publique avec les connecteurs Google Slides (création d'image à la place du cadre `Logo`, mêmes position et hauteur) et Google Docs (image en ligne dans le bandeau), en prenant la version lisible sur le fond concerné.
3. Relire les fichiers convertis : polices appliquées, couleurs, logos, aucun bloc décalé. Une police remplacée par Google à la conversion est signalée.

## 7. Vérifier

```bash
cd masters && soffice --headless --convert-to pdf *.pptx *.docx && pdftoppm -r 50 -png <fichier>.pdf page
```

Regarder chaque page rendue et contrôler :
- aucun texte qui déborde de son cadre, aucun texte illisible sur son fond ;
- les ratios du rapport `contraste` du profil, tous au-dessus du seuil ;
- `champs.json` : aucun champ ne contient de faute de frappe, `{{MARQUE}}` et `{{SITE}}` sont bien remplis ;
- aucun fait sur le produit (fonction, chiffre, prix, compatibilité) écrit en dur.

## 8. Livrer

Compte rendu court :
- liens vers les deux masters (ou fichiers envoyés) ;
- palette et polices retenues, avec leurs sources ;
- liste `a_verifier` ;
- mode d'emploi en trois lignes : copier le master, remplacer les champs, supprimer la slide 0 et les consignes.

## Règles de rédaction

- Reprendre le ton du site ; vouvoiement si rien n'est clair.
- Décrire ce que l'utilisateur fait, pas la technique, sauf pour un public technique.
- Pas de tirets cadratins dans les textes.
- Ce qui n'est pas connu reste en champ `{{...}}` ou `[à compléter]`.
- Logos repris tels quels, jamais redessinés.
- Aucun concurrent cité ni dénigré dans les gabarits.

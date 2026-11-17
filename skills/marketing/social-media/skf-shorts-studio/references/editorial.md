# Ligne éditoriale d'un short qui accroche

Un short se joue en **2 secondes** (on reste ou on swipe), se regarde **sans le son** la
plupart du temps, et se termine par **une seule** action. Tout ce qui suit sert ces trois
contraintes.

## 1. Les 7 règles

1. **Une idée par vidéo.** Si l'idée ne tient pas en une phrase de 12 mots, il y a deux vidéos.
2. **L'accroche nomme la douleur ou la promesse du spectateur**, jamais le nom du produit.
   « Tes devis te prennent 3 heures ? » bat « Découvrez Acme ».
3. **Une idée par écran, 7 mots au plus**, un seul mot surligné (le mot qui porte la promesse
   ou la douleur : un chiffre, un verbe, une durée).
4. **Coupe toutes les 1,5 à 3 secondes.** Total 15 à 35 s. Plus court que prévu, toujours.
5. **Le produit apparaît vite** (avant 40 % de la durée) et **en vrai** : capture d'écran,
   démo, pas une illustration générique.
6. **Une preuve** : un chiffre sourcé, un avant/après, une démo qui montre le résultat.
7. **Fin = une action**, une seule, avec le moyen de la faire (URL courte, « lien en bio »).

## 2. Les accroches (scène `hook`)

Choisir la formule qui colle à l'idée et au ton de la marque ; l'écrire avec les mots du
public (`idea.pain`). Le texte de l'accroche **est** le titre de la cover (ou très proche).

| Formule | Exemple (SaaS de devis) | Quand |
|---|---|---|
| Question douleur | « Tes devis te prennent **3 heures** ? » | douleur concrète et mesurable |
| Arrête de… | « Arrête de **recopier** tes devis » | tâche répétitive connue de tous |
| Tâche en durée courte | « Un devis complet en **30 secondes** » | promesse de vitesse prouvable |
| Chiffre choc | « **4 800** artisans ne font plus leurs devis le soir » | chiffre sourcé et surprenant |
| Ce que personne ne dit | « Personne ne te dit que tes devis te coûtent **des clients** » | idée, conviction, contre-pied |
| POV | « POV : ton devis part **avant** que le client raccroche » | public jeune, ton léger |
| Avant / Après | « **Avant** : 3 h. **Après** : 30 s. » | gain spectaculaire et visuel |
| Mythe / Réalité | « Un bon devis, c'est **long** à faire. Faux. » | idée reçue à casser |
| Liste | « **3 choses** qu'Acme fait à ta place » | plusieurs bénéfices égaux |
| Secret / astuce | « L'astuce des artisans qui **signent** plus vite » | conseil utile, produit en solution |

À éviter : « Découvrez… », « Nouveau ! » seul, une question à laquelle on répond non, le nom
du produit en premier mot, un jargon que le public n'emploie pas, un emoji à la place du sens.

## 3. Les structures (angles)

Durées indicatives en secondes ; `scene.type` du storyboard entre crochets.

**A. Problème → solution** (le plus sûr pour un SaaS) — 20 à 25 s
accroche douleur [hook 2] → on enfonce le clou [statement 2,5, `strike` sur l'ancienne
façon] → révélation [reveal 2] → démo [media 4–6, téléphone ou navigateur] → preuve
[stat 2,5 ou list 3,5] → action [cta 3]

**B. Avant / Après** — 15 à 20 s
avant [hook 2, média sombre en fond] → après [media 4] → le chiffre de l'écart [stat 2,5]
→ action [cta 3]

**C. Liste « 3 choses »** — 20 à 30 s
promesse de liste [hook 2] → chaque point avec son visuel [media 3 × 3] ou une liste
animée [list 4] → révélation [reveal 2] → action [cta 3]

**D. Démo express** — 15 à 25 s
« Regarde » [hook 1,5] → démo continue [media 8–12, vidéo] → résultat [statement 2] →
action [cta 3]

**E. Conviction** (illustrer une idée, sans démo) — 15 à 25 s
contre-pied [hook 2] → argument 1 [statement 2,5] → argument 2 [statement 2,5] → la
conclusion qui retourne la situation [statement 2,5] → qui le rend possible [reveal 2] →
action [cta 3]

Choisir l'angle d'après les sources : une démo vidéo forte → D ou A ; un chiffre fort → B
ou une accroche chiffre ; plusieurs bénéfices sans démo → C ; une idée sans produit
visible → E.

## 4. Écrire les écrans

- Verbes d'action, présent, deuxième personne (selon `brand.tone` : tu ou vous).
- Chiffres concrets et sourcés (`kit.facts`) ; jamais d'arrondi flatteur.
- `highlight` : le **mot qui porte la promesse** (une durée, un chiffre, un verbe fort),
  1 à 3 mots, présent tel quel dans le texte.
- `strike` : l'ancienne façon de faire, rayée après une demi-seconde.
- `emoji` : un seul, seulement s'il ajoute une émotion (😩 douleur, 🤯 surprise, ✅ résultat).
- La dernière image renvoie à la première (boucle) : même mot, même couleur, ou une question
  qui relance.
- Musique : énergique et sous licence (`kit.assets` audio en `own`, `royalty-free`, `cc0`,
  `cc-by` avec crédit). Aucune musique sûre : vidéo sans musique, l'utilisateur ajoutera un
  son de la bibliothèque de la plateforme à l'envoi.

## 5. La cover

La cover se voit **en petit**, dans une grille ou un fil, à côté de dizaines d'autres. Elle
doit se lire en **une demi-seconde**.

- **Titre de 2 à 5 mots**, la promesse de l'accroche, en très gros (≥ 9 % de la largeur par
  lettre de hauteur), un mot sur le bloc d'accent.
- **Un visuel du produit** (capture dans un téléphone, interface en gros plan) ou rien —
  jamais une image générique.
- **Badge** facultatif, 1 à 2 mots : « NOUVEAU », « EN 30 S », « DÉMO », « AVANT/APRÈS ».
- Logo discret en haut ; aucun autre texte.
- Titre et visuel dans le **carré central** (y 420–1500 sur 1080×1920) : Instagram recadre la
  grille en 3:4, certains affichages en 1:1.
- La **première image de la vidéo** ressemble à la cover (même texte, même couleur) : X,
  Bluesky, TikTok et souvent YouTube prennent cette image comme vignette.

Formules de titres de cover qui marchent :

| Formule | Exemple |
|---|---|
| Durée | « Tes devis en **30 secondes** » |
| Verbe + objet | « **Stop** aux devis du soir » |
| Chiffre | « **3 h** gagnées par semaine » |
| Avant/Après | « 3 h → **30 s** » |
| Question courte | « Encore **3 h** de devis ? » |
| Contre-pied | « Ton devis est **trop long** » |

## 6. Ce qu'on ne fait jamais

- Un chiffre, une fonctionnalité, un client, un prix absents de `kit.facts`.
- Un logo ou une marque tierce sans droit ; une musique sans licence.
- Une promesse que la démo ne montre pas (piège à clic = abonnés perdus).
- Du texte dans les zones d'interface (le template les évite : ne pas forcer).

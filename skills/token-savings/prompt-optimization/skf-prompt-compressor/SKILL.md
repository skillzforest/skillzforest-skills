---
name: skf-prompt-compressor
description: Compresse un prompt long pour économiser des tokens : retire répétitions et remplissage, garde les instructions et le contexte utiles, et chiffre le gain obtenu.
---

# Prompt Compressor

Objectif : produire une version plus courte d'un prompt (system prompt, instructions de projet, SKILL.md, prompt d'agent, consigne ponctuelle) qui donne au modèle exactement les mêmes consignes, avec moins de tokens. Le sens prime sur le gain : un prompt plus court mais qui fait perdre une contrainte est un échec.

## Quand l'utiliser

Dès que l'utilisateur demande de compresser, raccourcir, alléger, optimiser en tokens ou « dégraisser » un prompt, des instructions de projet ou une skill. Le prompt peut être collé dans le message, joint en fichier (.md, .txt, .docx, .pdf) ou désigné dans une conversation précédente.

## Entrées

1. Le prompt source. S'il est absent, le demander en une phrase.
2. Le niveau de compression. Par défaut : **standard**. Ne poser la question que si le prompt est très long (plus de ~3 000 tokens) ou critique.
   - **Léger** (~15-30 %) : suppression du remplissage et des doublons uniquement, formulation conservée.
   - **Standard** (~30-50 %) : léger + reformulation concise, fusion des consignes proches, passage de la prose en listes courtes.
   - **Agressif** (~50 %+) : standard + réduction des exemples, style télégraphique, suppression des justifications. Toujours signaler les risques.

## Étape 1 : cartographier le prompt

Avant de couper quoi que ce soit, lister chaque élément porteur de sens :
- rôle / identité attribuée au modèle ;
- objectif et livrable attendu ;
- contraintes et interdits (surtout les négations : « ne jamais », « sauf si ») ;
- format de sortie (structure, longueur, langue, ton) ;
- contexte métier indispensable ;
- exemples, et ce que chacun illustre ;
- éléments techniques à préserver à l'identique (voir Étape 3).

Cette liste sert de checklist de vérification à l'Étape 4.

## Étape 2 : appliquer les techniques de compression

Par ordre de priorité (du plus sûr au plus risqué) :

1. **Supprimer le remplissage** : formules de politesse, « je voudrais que tu », « il est très important de noter que », « n'hésite pas à », méta-commentaires sur le prompt lui-même, encouragements.
2. **Dédoublonner** : une consigne répétée à plusieurs endroits n'est gardée qu'une fois, à l'endroit le plus logique. Si la répétition servait à insister, la remplacer par un seul marqueur clair (ex. « Impératif : »).
3. **Fusionner** les consignes proches en une seule phrase ou une seule puce.
4. **Condenser la prose** : phrases longues en puces courtes, voix active, verbes à l'impératif, suppression des adverbes vides (vraiment, simplement, bien sûr).
5. **Factoriser** : regrouper sous un titre commun ce qui partage un même contexte plutôt que de le répéter à chaque ligne.
6. **Réduire les exemples** (standard et agressif) : garder un exemple par comportement distinct, raccourcir les parties de l'exemple qui n'illustrent rien. Ne jamais supprimer le seul exemple qui définit un format de sortie.
7. **Retirer les justifications** (agressif seulement) : les « parce que… » qui n'aident pas le modèle à trancher un cas limite. Garder celles qui expliquent une règle non évidente, car elles guident la généralisation.

À éviter :
- abréviations obscures ou jargon inventé qui gagnent quelques tokens mais nuisent à la compréhension du modèle ;
- suppression d'articles et de mots grammaticaux au point de rendre une phrase ambiguë ;
- changement de la langue du prompt ;
- ajout de tirets cadratins : utiliser deux-points, virgules ou parenthèses.

## Étape 3 : éléments à préserver à l'identique

Ne jamais modifier :
- variables et placeholders (`{{client}}`, `{nom}`, `$INPUT`, `[À COMPLÉTER]`) ;
- balises XML / Markdown utilisées comme structure (`<context>`, `<output_format>`) ;
- noms propres, noms d'outils, noms de fichiers, URLs, chemins, identifiants ;
- valeurs chiffrées, seuils, dates, pourcentages ;
- blocs de code, regex, schémas JSON, commandes ;
- chaînes que le modèle doit reproduire mot pour mot (libellés, mentions légales, messages types) ;
- frontmatter d'une skill (`name`, `description`) : le corps peut être compressé, la description seulement en mode agressif et sans perdre ses déclencheurs.

## Étape 4 : vérifier

Reprendre la checklist de l'Étape 1 et confirmer que chaque élément est présent dans la version compressée, avec le même sens. Points de contrôle :
- toutes les négations et exceptions sont toujours là ;
- l'ordre de priorité entre règles n'a pas changé ;
- aucune nouvelle ambiguïté n'a été introduite ;
- le prompt compressé reste lisible par un humain qui devra le maintenir.

Si un élément a été retiré volontairement (exemple redondant, justification), il doit apparaître dans la liste des suppressions.

## Étape 5 : mesurer le gain

Compter les tokens avant et après :
- Si Bash est disponible, tenter `pip install tiktoken --break-system-packages` puis compter avec l'encodage `cl100k_base` (approximation proche des tokenizers récents ; préciser que c'est une estimation, le tokenizer de Claude diffère légèrement).
- Sinon, estimer : nombre de caractères / 4 pour l'anglais, / 3,5 pour le français. Indiquer « estimation ».

Calculer : tokens avant, tokens après, tokens économisés, % de réduction.

## Format de restitution

1. **Le prompt compressé**, complet, dans un bloc de code copiable (pas en fichier, sauf si l'utilisateur le demande ou si le prompt source était un fichier à rendre dans son format).
2. **Bilan** en tableau court :

| | Avant | Après | Gain |
|---|---|---|---|
| Tokens (estim.) | … | … | … % |
| Caractères | … | … | … % |

3. **Ce qui a été retiré ou fusionné** : 3 à 8 puces, par catégorie (remplissage, doublons, exemples, justifications).
4. **Points de vigilance** (seulement s'il y en a) : passages où la compression pourrait changer le comportement, ou ambiguïtés présentes dès l'original que l'utilisateur pourrait clarifier.
5. Une ligne pour proposer, si pertinent, le niveau supérieur ou inférieur de compression.

## Règles générales

- Livrer directement le résultat, sans demander de validation intermédiaire.
- Si le prompt est déjà concis (gain possible inférieur à ~10 %), le dire franchement et proposer seulement les quelques retouches utiles plutôt que de forcer une réécriture.
- Si le prompt contient des contradictions, ne pas les trancher en silence : garder les deux et les signaler en point de vigilance.
- Répondre dans la langue de l'utilisateur ; le prompt compressé reste dans la langue du prompt source.

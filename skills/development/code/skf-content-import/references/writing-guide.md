# Rédiger une fiche produit de skill

Le lecteur n'est pas forcément développeur. Il veut savoir en dix secondes si la skill
règle **son** problème, puis comment s'en servir.

## Principes

- **Concret avant abstrait.** Ouvrir sur une situation réelle (« Votre designer vous
  envoie la maquette… »), pas sur une catégorie (« Un outil puissant de… »).
- **Des faits, pas des adjectifs.** « Exporte en WebP au poids demandé » plutôt que
  « des images optimisées ». Supprimer : puissant, révolutionnaire, ultime, magique,
  seamless, boost, game-changer, en quelques clics.
- **Ne rien promettre que la skill ne fait pas.** Tout ce qui est écrit doit se
  retrouver dans son SKILL.md ou ses scripts. Les prérequis (Python, clé d'API, outil
  externe) sont dits, pas cachés.
- **Le nom de la skill** apparaît dans le prompt d'usage tel qu'il s'invoque
  (`skf-design-extractor`), le nom commercial ailleurs (« Design Extractor »).
- **Phrases courtes**, voix active, « vous » en français, « you » en anglais.
- **Chaque langue est écrite pour elle-même** : idiomes, ponctuation (espace avant
  `: ? !` en français, guillemets « » en français et “ ” en anglais).

## Par champ

| Champ | Ce qu'il doit faire |
|---|---|
| Nom affiché | 2 à 4 mots, ce que c'est (« Design Extractor », « Cadrage fonctionnel ») |
| Accroche (headline) | Une phrase : le besoin du lecteur, souvent en question (« Vous voulez … ? ») |
| Description | 600–1 200 caractères : scénario avant, ce que fait la skill, ce qu'on obtient, prérequis |
| Bénéfices (3) | Un gain chacun, ≤ 80 caractères idéalement, commence par le gain |
| En bref (skill) | 4–6 blocs : contenu ou garantie concrète ; titre ≤ 40 caractères, une ligne |
| Ce que vous pouvez faire | 3 résultats concrets que l'utilisateur obtient |
| Usage : instructions | Où ouvrir l'agent, quels fichiers avoir sous la main, se termine par « collez ce prompt : » |
| Usage : prompt | Une vraie demande, autonome, qui nomme la skill et ses entrées |
| Usage : explication | Ce qui se passe, étape par étape, et ce qui est produit ; une variante courte si utile |
| Texte alternatif média | Décrit ce que montre l'image/la vidéo, pas « image de la skill » |
| Tags | Mots que l'utilisateur taperait dans la recherche |

## Pack

- L'accroche vend le **résultat de bout en bout**, pas la somme des skills.
- La description raconte le parcours : étape 1 produit X, que l'étape 2 utilise…
- `skills_subtitle` : une phrase qui introduit la liste (« Six skills, dans l'ordre où
  vous vous en servez »).
- Un prompt d'usage par skill (`skill_usage`), chacun autonome.

## Visuels

- `glyph` : une ou deux lettres du nom, ou un emoji qui évoque l'action — lisible à
  36 px, sans texte autour.
- La vidéo reprend l'accroche, le prompt (abrégé s'il dépasse ~140 caractères) et les
  3 bénéfices (ou les skills du pack) : les mêmes mots que la page.

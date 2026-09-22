# SkillzForest Workflows

Ce dépôt est conçu en mode skill-first : chaque `SKILL.md` reste atomique, lisible, et autonome. Les workflows ne remplacent pas les skills ; ils décrivent l’ordre logique d’orchestration entre plusieurs skills selon le contexte de projet.

## 1. Distinction claire

- Skill : capacité métier ou documentaire autonome (ex. `av-cadrage-fonctionnel`, `av-devis`), rangée sous `skills/<famille>/`.
- Workflow : séquence de compétences à enchaîner selon un besoin projet.
- Pack : produit commercial qui référence plusieurs skills cohérentes (ex. `packs/presales/pack.json`), sans jamais en dupliquer le contenu.
- Bundle : ensemble de plusieurs packs commercialisés ensemble.
- Runtime : environnement cible (Claude Code, Codex, Cursor…) qui adapte ou génère le format d'installation à partir de `skills/`.
- MCP / connecteurs : accès Drive, Sheets, Miro, Docs, Slides, etc.
- LLM / runtime : moteur de raisonnement qui décide de déclencher une skill ou une suite de skills.

Les skills ne doivent pas embarquer de logique d’orchestration. Une skill ne contient pas de “workflow” interne ; elle décrit son périmètre, ses entrées, ses gardes-fous et sa sortie.

## 2. Graphique de dépendances réel du repo

Les dépendances ci-dessous sont tirées des docstrings et des règles propres aux skills existants.

- `av-init-projet`
  - initialise l’arborescence projet et les documents de base
  - ouvre la voie à `av-cadrage-fonctionnel` et `av-cadrage-plateforme`

- `av-cadrage-fonctionnel`
  - dépend du projet et des entrées client
  - alimente `av-parcours-miro`
  - alimente `av-presentation-client`
  - alimente le chiffrage (`av-devis`, `av-devis-tma`)

- `av-cadrage-plateforme`
  - dépend des documents techniques et des décisions de conception
  - alimente `av-schema-logique`
  - alimente `av-schema-physique`
  - alimente le chiffrage (`av-devis`, `av-devis-tma`)
  - alimente `av-presentation-client`

- `av-parcours-miro`
  - dépend du cadrage fonctionnel
  - sert d’input UX pour la présentation client

- `av-devis`
  - dépend du cadrage fonctionnel et du cadrage plateforme
  - est un input de `av-presentation-client`

- `av-devis-tma`
  - dépend du cadrage plateforme et du périmètre fonctionnel
  - est un input de `av-presentation-client`

- `av-presentation-client`
  - dépend des livrables produits : cadrage fonctionnel, cadrage plateforme, devis, TMA, parcours Miro, démo

- `av-compte-rendu-reunion`
  - est transverse et indépendant
  - peut être déclenché à n’importe quel moment du projet pour documenter les décisions et suivre les actions

## 3. Workflow principal recommandé

Le workflow d’avant-vente complet est le suivant :

1. Initialiser le projet
2. Cadrer le besoin fonctionnel
3. Cadrer la plateforme / l’architecture
4. Générer les parcours utilisateurs
5. Chiffrer le projet (forfait + TMA)
6. Préparer la présentation client
7. Déclencher des comptes rendus de réunion selon les points de décision

Ce n’est pas une chaîne linéaire rigide : les étapes 2 et 3 peuvent être menées en parallèle, puis converger vers le chiffrage et la présentation.

## 4. Dossiers de workflow

Les workflows concrets du dépôt sont rangés sous `workflows/` :

- `workflows/avant-vente-complete/WORKFLOW.md`
- `workflows/cadrage-fonctionnel/WORKFLOW.md`
- `workflows/cadrage-technique/WORKFLOW.md`
- `workflows/ux-parcours/WORKFLOW.md`
- `workflows/chiffrage/WORKFLOW.md`
- `workflows/presentation-client/WORKFLOW.md`

## 5. Règles de gouvernance

- Une workflow décrit une orchestration, pas des détails métier internes.
- Une skill documente une capacité que l’on peut déclencher de façon autonome.
- Une workflow ne doit pas dupliquer les gardes-fous déjà présents dans les skills.
- Une workflow doit toujours expliciter ses dépendances et ses livrables de sortie.
- `av-compte-rendu-reunion` est un “transversal” : il peut être ajouté à n’importe quel workflow sans modifier sa logique de base.

## 6. Exemple de commande de déclenchement

Le runtime peut utiliser une logique de type :

- “nouveau prospect” → `av-init-projet`
- “cadrer le besoin” → `av-cadrage-fonctionnel`
- “cadrer la plateforme” → `av-cadrage-plateforme`
- “parcours utilisateurs” → `av-parcours-miro`
- “devis / chiffrage” → `av-devis` et éventuellement `av-devis-tma`
- “présentation client” → `av-presentation-client`
- “CR de réunion” → `av-compte-rendu-reunion`

## 7. Sortie attendue

Les workflows ne remplacent pas les livrables métiers. Ils servent à structurer l’ordre des actions, la dépendance entre documents et la cohérence de la chaîne avant-vente.

## 8. Concept formel d'un workflow

Un workflow, au sens SkillzForest :

- référence plusieurs skills par leur nom (jamais par copie de fichiers) ;
- définit un ordre ou une orchestration entre elles ;
- ne duplique jamais leur contenu, leurs entrées ou leurs garde-fous ;
- peut appartenir à un ou plusieurs packs commerciaux (ex. `avant-vente-complete` appartient au Pre-Sales Pack).

Exemple de manifeste **illustratif** (aucun `workflow.json` de ce type n'existe encore dans ce dépôt — les workflows actuels sont documentés en Markdown sous `workflows/<nom>/WORKFLOW.md`, ce qui suffit tant qu'aucune orchestration automatisée n'est nécessaire) :

```json
{
  "id": "avant-vente-complete",
  "name": "Avant-vente complète",
  "packs": ["presales"],
  "steps": [
    { "skill": "av-init-projet" },
    { "skill": "av-cadrage-fonctionnel" },
    { "skill": "av-cadrage-plateforme" },
    { "skill": "av-parcours-miro" },
    { "skill": "av-devis" },
    { "skill": "av-devis-tma", "optional": true },
    { "skill": "av-presentation-client" }
  ]
}
```

## 9. Format minimal (steps à plat)

Quand aucune étape n'est optionnelle ni conditionnelle, `steps` peut simplement lister des ids de skills dans l'ordre d'exécution. Exemple **purement conceptuel** — `product-spec`, `ux-flow`, `board-ticket`, `dev-implementation`, `qa-acceptance` et `release-checklist` n'existent pas encore dans `skills/`, donc ce workflow n'est pas créé comme actif :

```json
{
  "id": "feature-to-production",
  "name": "Feature to Production",
  "steps": [
    "product-spec",
    "ux-flow",
    "board-ticket",
    "dev-implementation",
    "qa-acceptance",
    "release-checklist"
  ]
}
```

Il servira de modèle le jour où les familles `product-*`, `ux-*`, `board-*`, `dev-*`, `qa-*` et `release-*` auront des skills réelles à référencer.

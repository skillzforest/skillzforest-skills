# Workflow : Growth Factory multi-projets

## Objectif

Faire tourner, pour plusieurs produits à la fois, une organisation de croissance et de développement commercial
pilotée par des tâches planifiées : veille, stratégie de canaux, campagnes, prospection, mesure. Le propriétaire garde
toutes les décisions engageantes et répond en un mot sur les issues GitHub.

## Prérequis

- Un dépôt privé « espace growth » (`skf-growth-profile/references/workspace.md`).
- Un board GitHub Projects créé par `skf-growth-tracker` (mode setup), ses identifiants dans `docs/board.json`.
- Un profil `growth.json` validé par projet (`skf-growth-profile`).
- Recommandé : le profil SEO de chaque site (`skf-seo-profile`), réutilisé tel quel ; un CRM (HubSpot) ; un outil
  de programmation de posts (Postiz via la Social Factory) quand les publications doivent partir sans intervention.

## Cycle d'une opportunité

1. `skf-market-intel` repère un fait sourcé et crée une issue Opportunité (statut À qualifier).
2. `skf-channel-strategy` (stratégie) ou `skf-prospect-pipeline` (organisation) la qualifie et la passe en Décision.
3. Le propriétaire commente APPROUVER, MODIFIER, REPORTER ou REFUSER.
4. `skf-growth-tracker` (mode decisions) enregistre la réponse.
5. `skf-campaign-studio` ou `skf-sales-outreach` prépare le livrable (statut Prêt) et demande la validation d'envoi.
6. Le propriétaire publie ou envoie (ou un outil programmé le fait après approbation), puis le signale.
7. `skf-growth-report` mesure et l'issue passe en Mesuré.

## Tâches planifiées types

Une tâche planifiée démarre une session neuve : tout ce qui doit survivre est dans l'espace growth ou le tracker.

| Tâche | Fréquence | Skills | Sortie |
|---|---|---|---|
| Market Intelligence | hebdomadaire | `skf-market-intel` (un sous-agent par projet), `skf-growth-tracker` | veille datée, opportunités |
| Prospects & Partenaires | hebdomadaire, projets B2B et partenaires en alternance | `skf-prospect-pipeline`, `skf-sales-outreach` | fiches CRM, décisions, brouillons |
| Campaign Studio | hebdomadaire | `skf-campaign-studio` (prepare puis distribute) | PR de campagne, publications à approuver |
| Ops quotidien | jours ouvrés | `skf-growth-tracker` (decisions), `skf-campaign-studio` (distribute), `skf-growth-report` (daily) | décisions enregistrées, point du jour |
| Revue hebdomadaire | hebdomadaire | `skf-growth-report` (weekly), `skf-channel-strategy` le premier de chaque mois | revue, page, brouillon d'email |

## Enchaînement entre tâches

Par défaut, chaque tâche reprend au créneau suivant ce que les autres ont laissé dans le tracker. Quand le runtime
permet à une tâche d'en déclencher une autre, l'Ops quotidien peut lancer tout de suite la tâche de préparation
concernée après un APPROUVER, en lui passant le lien de l'issue. Garde-fous : seul l'Ops déclenche, trois
déclenchements par exécution au plus, une tâche déclenchée n'en déclenche aucune.

## Validation humaine

Automatique : recherche, analyse, qualification, brouillons, issues, PR dans l'espace growth, rapports.
Toujours soumis au propriétaire : envoi, publication, création de compte, dépense, changement de positionnement
(`skf-growth-profile/references/guardrails.md`).

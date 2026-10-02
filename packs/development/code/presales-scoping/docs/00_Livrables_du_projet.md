# 00 — Livrables du projet

> **Repère de lecture**
> **Livrable** = va au client. **Support** = étape de travail (non remis). **Référence** = matière première du projet (jamais remise).

Ce fichier recense, rôle par rôle, ce qui est produit, ce qui est remis au client, et ce qui reste interne. Il sert d'index réutilisable : pour un nouveau client, on repart de cette structure pour cadrer en ~20 min ce qui devra être produit.

---

## Vue d'ensemble par rôle

| Rôle | Livrable client | Support de travail | Référence mobilisée |
|---|---|---|---|
| 1 — Business Analyst | Contribue au *Cadrage fonctionnel* | Synthèse du besoin, catalogue fonctionnel, points d'ambiguïté | PRD client, 01_Vision |
| 2 — Consultant Cadrage | Contribue au *Cadrage fonctionnel* | Synthèse cadrage, questions, recommandations, arbitrages MVP | PRD client, 01, 02 |
| 3 — Product Owner | Contribue au *Cadrage fonctionnel* | Personas, backlog MVP, définition MVP | 02_Fonctionnel_MVP |
| 4 — UX Designer | Contribue au *Cadrage fonctionnel* | User Journey Map, UX Specification, maquettes, prototype HTML | 02_Fonctionnel_MVP |
| **4bis — Développeur Démo** | **Démo interactive publique (GitHub Pages)** | Repo GitHub, code du prototype, assets | UX Spec (rôle 4) |
| 5 — Architecte / CTO | **Note de cadrage de la plateforme** (Google Doc) | 4 tableaux HTML, 2 schémas Excalidraw, diagrammes Mermaid | 03_Archi, 04_Décisions, gabarits |
| 6 — DevOps / DevSecOps | Contribue à la *Note de cadrage plateforme* et à la présentation | Pipeline CI/CD, plan d'environnements, plan d'exploitation | 03, 04 |
| 7 — Delivery Manager | Contribue à la *Présentation avant-vente* | Roadmap MVP (4 phases) | Définition MVP, archi |
| 8 — Responsable Chiffrage | Contribue à la *Présentation avant-vente* | Estimation budgétaire, TMA mensuelle/annuelle | MVP, UX, archi (tableaux rôle 5), roadmap |
| 9 — Consultant Avant-Vente | **Présentation client** (deck) | — | Tous les livrables amont |

---

## Détail par rôle

### Rôle 1 — Business Analyst
- **Livrable client** : aucun en propre ; alimente le *Cadrage fonctionnel de l'application SaaS*.
- **Supports** : synthèse du besoin (contexte, objectifs, enjeux, périmètre) ; catalogue fonctionnel ; tableau des points d'ambiguïté ; hypothèses initiales.
- **Référence** : PRD client (`PRD_Brasserie_AI_V1`), `01_Vision_Produit_SaaS_Brasseurs`.

### Rôle 2 — Consultant Cadrage Avant-Vente
- **Livrable client** : aucun en propre ; alimente le *Cadrage fonctionnel*.
- **Supports** : synthèse cadrage (maturité par domaine) ; questions de cadrage ; recommandations ; arbitrages MVP ; hypothèses de chiffrage.
- **Référence** : PRD client, `01_Vision`, `02_Fonctionnel_MVP`.

### Rôle 3 — Product Owner Agile
- **Livrable client** : aucun en propre ; alimente le *Cadrage fonctionnel*.
- **Supports** : personas ; backlog MVP (Epic / User Story / priorité MoSCoW) ; définition MVP (inclus, reporté, critères de succès).
- **Référence** : `02_Fonctionnel_MVP_SaaS_Brasseurs`.

### Rôle 4 — UX Designer
- **Livrable client** : aucun en propre ; alimente le *Cadrage fonctionnel*.
- **Supports** : User Journey Map ; UX Specification (écrans, composants, interactions, navigation, règles métier) ; maquettes / prototype HTML interactif ; schéma de la boucle QR (SVG).
- **Référence** : `02_Fonctionnel_MVP`.

### Rôle 4bis — Développeur Démo *(nouveau)*
- **Livrable client** : **démo interactive publique**, déployée sur **GitHub Pages**, accessible par simple URL. Sert d'asset avant-vente manipulable par le prospect.
- **Supports** : dépôt GitHub (code du prototype, historique) ; assets ; configuration du déploiement (GitHub Pages / Actions).
- **Référence** : UX Specification et maquettes (rôle 4).

### Rôle 5 — Architecte Solution / CTO
- **Livrable client** : **Note de cadrage de la plateforme** (Google Doc), produite à partir du gabarit `Cadrage_plateforme_template`. Distincte du cadrage fonctionnel.
- **Supports** : 4 tableaux HTML (référentiel des composants, matrice de flux, composants serveurs, services tiers) ; 2 schémas Excalidraw (architecture logique, infrastructure physique) ; diagrammes Mermaid (vue applicative, vue serveur).
- **Référence** : `03_Architecture_Technique_Cible`, `04_Decisions_et_Hypotheses_Architecture`, gabarits (tableaux HTML, templates Excalidraw, `Cadrage_plateforme_template`).

### Rôle 6 — DevOps / DevSecOps
- **Livrable client** : aucun en propre ; alimente la *Note de cadrage plateforme* (exploitation) et la *Présentation avant-vente*.
- **Supports** : pipeline CI/CD (tests, lint, build, analyse sécurité, scan dépendances/images, secrets, validation prod) ; plan d'environnements (dev, préprod, prod) ; plan d'exploitation (supervision, alertes, incidents).
- **Référence** : `03_Archi`, `04_Décisions`.

### Rôle 7 — Delivery Manager Agile
- **Livrable client** : aucun en propre ; alimente la *Présentation avant-vente*.
- **Supports** : roadmap MVP en 4 phases (cadrage & UX, développement, tests & recette, mise en production) — objectif, durée, livrables, dépendances par phase.
- **Référence** : définition MVP (rôle 3), architecture (rôle 5).

### Rôle 8 — Responsable Chiffrage
- **Livrable client** : aucun en propre ; alimente la *Présentation avant-vente*.
- **Supports** : synthèse (coût projet HT, durée, TMA mensuelle/annuelle) ; détail par lot/phase/activité/profil ; hypothèses, exclusions, dépendances client.
- **Référence** : MVP, UX, architecture (tableaux serveurs et services tiers du rôle 5), roadmap.

### Rôle 9 — Consultant Avant-Vente
- **Livrable client** : **Présentation client** (deck) assemblant contexte, enjeux, recommandations, personas, user journey, MVP, UX, architecture, organisation, roadmap, budget, TMA, risques, conclusion.
- **Supports** : —
- **Référence** : l'ensemble des livrables et supports amont.

---

## Livrables client consolidés (ce qui est réellement remis)

1. **Cadrage fonctionnel de l'application SaaS** — synthèse des rôles 1 à 4 (Google Doc / Word).
2. **Démo interactive publique** — rôle 4bis (GitHub Pages).
3. **Note de cadrage de la plateforme** — rôle 5 (Google Doc, gabarit `Cadrage_plateforme_template`). Intègre la partie exploitation du rôle 6.
4. **Présentation / proposition avant-vente** — rôle 9 (deck). Intègre la roadmap (rôle 7), le budget et la TMA (rôle 8), les risques.

---

## Fichiers de référence du projet (jamais remis)

- `01_Vision_Produit_SaaS_Brasseurs.md`
- `02_Fonctionnel_MVP_SaaS_Brasseurs.md`
- `03_Architecture_Technique_Cible.md`
- `04_Decisions_et_Hypotheses_Architecture.md`
- PRD client (`PRD_Brasserie_AI_V1`)
- `Guide_QR_code_augmente_web.pdf`
- Gabarits : tableaux HTML, templates Excalidraw (architecture logique, infrastructure physique), `Cadrage_plateforme_template`, script générateur Word réutilisable.

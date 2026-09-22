---
name: av-nom-de-domaine
description: >-
  Trouve et sécurise le nom de domaine / nom de marque d'un projet via le MCP GoDaddy. Analyse la graine et le contexte projet, puis — si la graine est prise ou en premium — propose des alternatives premium, prononçables FR/EN, à connotation française, non clichées et transversales (pas enfermées dans une seule verticale produit). Règle d'or : ne JAMAIS proposer un nom sans avoir vérifié sa disponibilité au préalable ; vérification en .com uniquement ; distingue standard (prix normal) / premium (dispo mais tarif marché secondaire élevé) / indisponible. Déclenche systématiquement ce skill dès que l'utilisateur veut un nom de domaine, un nom de marque, vérifier si un domaine est libre, ou trouver un nom pour une plateforme / un produit — « trouve un nom de domaine pour X », « vérifie si X.com est libre », « propose un nom de marque pour le projet », « un nom pour la plateforme X ». Suite Avant-Vente SkillzForest (préfixe av-).
compatibility: >-
  Connecteur MCP GoDaddy (domains_check_availability pour la vérification,
  domains_suggest en appoint de génération). Sans ce connecteur, le skill ne
  peut pas vérifier — le signaler et proposer d'activer GoDaddy dans le menu
  des outils.
---

# av-nom-de-domaine — Nom de domaine & marque du projet

Propose et **vérifie** des noms de domaine premium et réellement disponibles, à partir du contexte du projet. Le livrable est une shortlist arbitrée (nom + prix + storytelling) prête à décision, plus un lien d'enregistrement GoDaddy. L'achat/enregistrement est **hors périmètre** (action à réaliser par l'utilisateur).

## Règle d'or (à ne jamais enfreindre)

1. **Vérifier avant de proposer.** Aucun nom n'est présenté à l'utilisateur sans être passé par `domains_check_availability` d'abord. Ceci vaut que le candidat vienne de mon brainstorm OU de `domains_suggest`.
2. **`.com` uniquement** en vérification (une seule extension).
3. **Trois états** à distinguer et à signaler : **Standard** (prix d'enregistrement normal) · **Premium** (disponible mais tarif marché secondaire, souvent plusieurs centaines à milliers d'€) · **Indisponible**.

## Charte de naming (critères d'un bon candidat)

- **Premium et non cliché** — sonorité soignée, évite les mots trop littéraux du métier.
- **Prononçable FR + EN**, court, mémorisable, facile à épeler (attention aux accents é/è ↔ e).
- **Marketable + storytelling** — le nom doit porter un récit exploitable en avant-vente (le geste, l'usage, la promesse).
- **Connotation française** par défaut (ajustable selon le projet).
- **Transversal à la catégorie, pas au sous-segment** — ne pas enfermer dans une verticale. Couvrir aussi les produits adjacents (ex. bière → aussi champagne, vin, spiritueux ; couvrir « la boisson de fête », pas « la bière »).

## Étape 1 — Point de départ (graine + contexte)

Récupérer la **graine** (nom pressenti) et le **contexte produit** : verticale(s), produits couverts, positionnement. Puiser dans les fichiers de contexte du projet (vision produit, cadrage fonctionnel) ; à défaut, demander la graine et la catégorie de produits à couvrir.

## Étape 2 — Vérifier la graine

`domains_check_availability` sur `{graine}.com`.
- **Standard** → la proposer directement (et éventuellement 2-3 variantes de confort).
- **Premium ou indisponible** → passer en génération d'alternatives (étape 3).

## Étape 3 — Générer des candidats

Constituer une salve de **~10 candidats** selon la charte de naming. Deux sources combinables :
- **Brainstorm dirigé** : racines françaises du champ produit (ex. *trinquer, cuvée, pétiller, brut, terroir, accord, millésime*) + suffixes brandables (`-ly`, `-o`, `-a`, `-ally`…), en visant la transversalité catégorie.
- **`domains_suggest`** en appoint pour élargir.

Privilégier des noms **inventés/brandables** : ils sortent plus souvent en **standard**, là où les mots français « pleins » sortent surtout en **premium**.

## Étape 4 — Vérifier AVANT de proposer (bulk)

Passer **tous** les candidats de la salve à `domains_check_availability` en une fois (liste séparée par virgules), **`.com` uniquement**. Ne retenir que les **réellement disponibles**. Itérer par salves successives jusqu'à obtenir de quoi arbitrer — viser au moins **3 standard** + quelques **premium** de qualité.

## Étape 5 — Restituer (shortlist arbitrée)

Présenter un tableau des candidats **vérifiés disponibles** :

`Nom (.com) | Prix (Standard/Premium) | Racine française | Storytelling / angle marketing | Transversalité`

Puis un **arbitrage clair** en deux temps :
- **Meilleur nom sur le fond** (même s'il est premium) — celui à la meilleure histoire de marque ;
- **Meilleure option au prix standard** — le meilleur rapport premium/prix.

Lister brièvement les **écartés (indisponibles)**. Fournir le **lien d'enregistrement GoDaddy** de chaque nom retenu (copier le deeplink exact renvoyé par l'outil, sans altérer les paramètres de tracking).

## Étape 6 — Formaliser (option)

Proposer de consigner le nom retenu comme **décision projet** (fichier de décisions/hypothèses du projet). Fournir le **texte prêt à coller** ; ne pas présumer que le fichier est mis à jour automatiquement. Rappeler que le domaine du SaaS est **distinct de tout domaine de marque de conseil** et qu'il reste à enregistrer par l'utilisateur.

## Garde-fous

- **Vérifier avant de proposer**, sans exception. Jamais de nom non vérifié dans la restitution.
- **`.com` uniquement** en vérification.
- **Signaler le surcoût premium** — ne jamais présenter un premium comme un enregistrement standard.
- **Ne pas enfermer dans une seule verticale** — couvrir la catégorie et ses produits adjacents.
- **Ne pas acheter/enregistrer** le domaine : renvoyer l'utilisateur vers l'enregistrement via le lien GoDaddy.
- **Ne rien inventer** sur le contexte produit : puiser dans les fichiers projet ou demander.

---
Documents et recommandations : Arnaud BRETON. Rédaction possible à la première personne (ma lecture, je recommande, je propose).

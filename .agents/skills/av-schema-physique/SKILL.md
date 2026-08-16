---
name: av-schema-physique
description: >-
  Produit le schéma d'INFRASTRUCTURE PHYSIQUE d'un projet (fichier .excalidraw) à partir du template bundlé : serveurs (rôle, capacité vCPU/RAM/disque, identifiant, adresses IP, composants logiciels), sous-réseaux (DMZ publique, applicative privée, données privée), et flux. Le skill ajuste les valeurs (marque, IP, capacités, tenants, technologies) et gère une variante sans redondance (retrait du replica). Déclenche systématiquement ce skill dès que l'utilisateur veut produire, générer ou mettre à jour le schéma physique, l'infrastructure physique, le schéma serveurs ou le schéma d'architecture physique d'un projet — « fais le schéma physique de X », « génère l'infra physique de X », « le schéma serveurs de X ». Suite Avant-Vente AI Factory (préfixe av-).
compatibility: Nécessite l'exécution de code (Node.js). Connecteur Google Drive pour déposer le fichier (optionnel).
---

# av-schema-physique — Schéma d'infrastructure physique (.excalidraw)

Génère le schéma **physique** (serveurs) d'un projet en éditant le template Excalidraw bundlé. Sortie : un `.excalidraw` prêt à ouvrir, ajuster et exporter.

## Règles verrouillées (doctrine — schéma physique)

Trois sous-réseaux : **DMZ publique**, **applicative privée**, **données privée**. Chaque serveur porte : rôle, capacité (vCPU · RAM · disque), identifiant, IP(s), composants logiciels. Règles :
- **Load balancer** justifié seulement avec **plusieurs frontaux** (flèches LB → chaque frontal). Logiciels du LB : Nginx, WAF.
- **Frontaux** : plusieurs serveurs actifs répartis par le LB ; cache HTTP par **Varnish sur les frontaux** (jamais de serveur de cache dédié).
- **Worker unique** : jamais dupliqué, non exposé, non rattaché au LB, nourri par la file d'attente.
- **Base unique multi-tenant hybride** (1 base, 1 schéma par tenant) + **réplica** (flèche double sens).
- **Adressage** : 1 IP privée par machine ; LB de bordure = 1 IP publique + 1 IP privée ; VIP partagée par cluster redondant.
- **Redondance masquable** : la variante sans redondance retire le replica et sa réplication.

## Étape 1 — Préparer les éditions

Template bundlé : `templates/architecture_physique.json`. Écrire `edits.json` :
```json
{
  "title": "{Projet}",
  "replace": {
    "10.0.1.11": "10.0.1.21",
    "4 vCPU · 8 Go · 100 Go SSD": "8 vCPU · 16 Go · 200 Go SSD",
    "Docker · Node.js · API Métier": "Docker · NestJS · API Métier"
  },
  "drop_redundancy": false
}
```
- `title` → `Infrastructure physique — {Projet}`.
- `replace` : substitutions **valeur par valeur** (IP, capacités, techno, tenants). Copier la chaîne exacte du template comme clé.
- `drop_redundancy: true` produit la **variante sans redondance** (retire le replica `db2`, sa flèche et le label « réplication »). Les flux principaux restent intacts.
- `remove_ids` / `remove_by_text` (optionnels) pour retirer un bloc précis.

## Étape 2 — Générer

```bash
node scripts/edit_excalidraw.js templates/architecture_physique.json edits.json Schema_physique_{Projet}.excalidraw
```
Le moteur applique les substitutions et le toggle **sans recalculer la mise en page**.

## Étape 3 — Déposer et insérer

1. Déposer le `.excalidraw` dans `{Projet}/02_Cadrage plateforme/Schémas d'architecture` (Drive : `create_file`, fichier conservé — pas de conversion), ou le livrer à l'utilisateur.
2. **Dire à l'utilisateur** : ouvrir dans Excalidraw, ajuster si besoin, exporter en image (PNG/SVG) et l'insérer dans la note de cadrage plateforme, **section 5** (emplacement `▢`). Insertion **manuelle**.

## Ajouter / retirer un serveur

Le moteur gère substitution + retrait (par id ou texte) + toggle redondance. **Ajouter** un frontal (ex. `srv-app-3`) implique de cloner un bloc (rectangle + texte + flèches) avec un décalage de position : le faire directement dans Excalidraw après génération (plus sûr que d'éditer le JSON à la main). Respecter alors la règle : LB → chaque nouveau frontal.

## Garde-fous

- **Template intouché** ; on édite vers un fichier de sortie.
- **Respecter les règles verrouillées** (worker unique, Varnish sur frontaux, LB seulement si ≥ 2 frontaux, base multi-tenant + réplica).
- **Ne rien inventer** : IP, capacités et tenants viennent du cadrage plateforme / de l'architecture cible.

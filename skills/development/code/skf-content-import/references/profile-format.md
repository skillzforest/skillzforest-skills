# Profil de CMS

Un profil décrit **un** CMS : la forme de la fiche, ses contraintes, ses médias, et
comment l'écrire. La skill ne connaît aucun CMS ; elle ne connaît que des profils.
Fichiers : `profiles/<id>.json`, ou n'importe quel chemin passé avec `--profile`.

Pour un nouveau CMS : copier `profiles/export.json` (sans API) ou
`profiles/strapi-example.json` (avec API), l'adapter, puis toujours commencer par
`push_content.py --dry-run`.

## Clés

| Clé | Rôle |
|---|---|
| `id`, `name`, `description` | Identification |
| `locales` | Langues à remplir, ex. `["fr", "en"]` |
| `title_field` | Champ du record utilisé comme titre de l'export |
| `defaults` | Valeurs à mettre dans le record quand rien d'autre ne s'impose |
| `guide` | Consignes de rédaction propres au CMS, à suivre à la lettre |
| `icons` | Liste de noms autorisés (référencée par `"enum": "@icons"`) |
| `fields` | Règles communes à tous les types |
| `media` | Emplacements média communs |
| `kinds.<skill\|pack>.fields` / `.media` | Règles et médias propres au type |
| `remotion` | `project`, `install_dir`, `brand`, `copy.<locale>`, `video_locale` |
| `libraries` | Listes à choisir (catégories, FAQ…) : `{"path", "query"}` en GET |
| `adapter` | Comment écrire : `http` ou `export` |

## Règles de champ (`fields`)

Le chemin part de la racine du fichier de contenu (`record.…`, `relations.…`) ;
`*` = chaque clé d'un objet ou chaque élément d'une liste.

```json
{"path": "record.page_content.texts.*.headline", "required": true, "type": "string",
 "min_length": 40, "max_length": 400}
```

`required` · `type` (`string`, `integer`, `number`, `boolean`, `array`, `object`) ·
`min_length` (avertissement) · `max_length` (`0` = ne pas envoyer, le CMS le calcule) ·
`min_items` (avertissement) · `max_items` · `item_max_length` · `enum` (liste ou
`"@<clé du profil>"`) · `pattern` (regex complète) · `locales: true` (l'objet doit avoir
toutes les langues du profil). Un texte contenant `TODO`, `TBD`, `lorem ipsum`… est
une erreur.

## Emplacements média (`media`)

```json
"cover": {"kind": "image", "required": true, "ratio": "1:1", "min_width": 512,
          "max_bytes": 1048576, "target_bytes": 51200, "formats": ["png", "webp"],
          "render": {"composition": "ProductCover", "format": "png", "scale": 1}}
```

`kind` est passé à l'upload (`{{media.kind}}`). `render` dit quelle composition des
templates Remotion produit le fichier : `ProductCover` (1:1), `ProductPoster` (16:9),
`ProductOutcome` (2:1), `ProductHero` (vidéo 1920×1080, 15 s). `format` : `png`,
`jpeg` (la qualité baisse jusqu'à tenir `target_bytes`/`max_bytes`) ou `webp`.

## Fichier de contenu (`content.json`)

```json
{
  "profile": "skillzforest",
  "kind": "skill",
  "source": {"path": "…", "name": "…"},
  "media": {"cover": {"file": "media/cover.png", "kind": "image"}},
  "record": {"slug": "…", "icon_url": "@media:cover", "…": "…"},
  "relations": {"child_ids": ["@lookup:catalog:skf-a", "@lookup:catalog:skf-b"]},
  "package": {"file": "skill.zip", "version": "0.1.0"},
  "pricing": {"price_amount": 29, "currency": "eur"}
}
```

- `record` est la fiche **dans la forme exacte du CMS** : c'est ce qui est envoyé.
- `@media:<emplacement>` → remplacé par le résultat de l'upload (URL ou id).
- `@lookup:<nom>:<clé>` → remplacé par la recherche `adapter.lookups.<nom>` (valeurs
  et clés d'objet).
- `relations`, `package`, `pricing` : facultatifs, utilisés par les étapes du profil.
- Chemins de fichiers relatifs au dossier du `content.json`.

## Adaptateur `http`

```json
"adapter": {
  "type": "http",
  "base_url_env": "CMS_URL", "base_url_default": "http://localhost:1337/api",
  "auth": {"type": "bearer", "token_env": "CMS_TOKEN"},
  "upload": {"path": "/upload", "query": {}, "field": "files", "result": "0.id"},
  "lookups": {"products": {"path": "/products", "query": {"q": "{{key}}"},
                           "items": "data", "match": "slug", "result": "id"}},
  "steps": [
    {"name": "find", "lookup": "products", "key": "{{record.slug}}", "save": "existing_id"},
    {"name": "create", "when": "!vars.existing_id", "method": "POST", "path": "/products",
     "body": "{{record}}", "save": {"item_id": "id"}},
    {"name": "update", "when": "vars.existing_id", "method": "PATCH",
     "path": "/products/{{vars.existing_id}}", "body": "{{record}}", "omit": ["slug"]}
  ]
}
```

- `auth.type` : `bearer`, `header` (avec `name`) ou `none`. Les secrets restent dans
  l'environnement, jamais dans le profil ni le contenu.
- Gabarits : `{{chemin}}` seul garde le type de la valeur (objet, liste, nombre) ;
  dans une chaîne plus longue, il est converti en texte. Contexte : `record` et
  `relations` (références résolues), `content` (le fichier brut), `package`
  (avec `path` absolu), `vars` (sauvegardes des étapes précédentes).
- `when` : `chemin` (vrai), `!chemin` (faux), `chemin == valeur`, `chemin != valeur`,
  combinables avec `&&`.
- Étape avec `file` : envoi multipart de ce fichier (champ `field`, défaut `file`).
- `save` : `{"variable": "chemin.dans.la.réponse"}`.
- `--dry-run` exécute les GET (recherches) et liste les écritures sans les faire.

## Adaptateur `export`

`{"type": "export", "out_dir": "content-export"}` : `record.json` (références média
remplacées par `media/<emplacement>.<ext>`), `content.md` lisible, et les médias.

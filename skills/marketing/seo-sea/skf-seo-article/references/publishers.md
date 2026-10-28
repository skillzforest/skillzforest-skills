# Validation and publication, per platform

`content.publish` says how an article reaches the owner for validation. In every case the agent **prepares** and
the owner **publishes**: nothing goes live without a human action.

| `content.publish` | The owner has | Validation | Publication |
|---|---|---|---|
| `repo` | the site's code in a Git repository | a pull request | merging it (and the site's deploy) |
| `cms` | a CMS with an API the agent may use | a **draft** in the CMS | « Publish » in the CMS |
| `markdown` | any back office, no API (or they prefer to paste) | the ticket at « To review » with a `.md` and an `.html` file | pasting into the CMS, then the ticket to « Published » with the URL |

Before the first call to a CMS, read its current API documentation for the version the site runs: field names and
endpoints change between major versions. Do one test call (list, read only) and stop with a clear message when it
fails (wrong address, expired credential, missing permission).

Credentials: an environment variable of the agent's cloud environment, named in `content.cms.tokenEnv` (and
`content.cms.userEnv` when the CMS needs a user name). Ask the owner for **the most limited credential that can
write drafts** — never an administrator's password.

## `repo`

The article is a file of the repository in `repo.blog.format`, in `repo.blog.dir`. Validation is the pull request
(`SKILL.md`, step 5). No blog section yet: `blog-scaffold.md` first.

## `cms`

`content.cms`:

| Field | Meaning |
|---|---|
| `type` | `wordpress`, `drupal`, `contentful`, `strapi`, `webflow`, `ghost`, `custom` |
| `baseUrl` | The site's or the API's address |
| `tokenEnv` | Environment variable holding the credential |
| `userEnv` | Optional. Variable holding the user name (WordPress, Drupal basic auth) |
| `options` | Per CMS: content type, collection, space, locale, categories… (below) |
| `editUrl` | Optional. Pattern of the draft's editor link, `{id}` replaced (shown to the owner) |

Body format: HTML for WordPress, Drupal, Webflow and Ghost; Markdown or the CMS's own rich-text format otherwise
(`article-format.md` gives both). Images: upload only when the CMS lets the credential do it; otherwise list them in
the ticket for the owner.

### WordPress

- Credential: a user with the **Contributor** role (writes drafts, cannot publish) and an **application password**
  (Users → Profile → Application Passwords). `userEnv` = the user name, `tokenEnv` = the application password.
- Create: `POST <baseUrl>/wp-json/wp/v2/posts`, basic auth, JSON `{title, content (HTML), excerpt, slug,
  status: "draft", categories: [ids], tags: [ids]}`. Category and tag ids: `GET /wp-json/wp/v2/categories?search=`.
- Meta description: written by an SEO plugin (Yoast, Rank Math, SEOPress…) whose field the REST API often does not
  expose; when it is not writable, put the description at the top of the ticket for the owner to paste.
- Multilingual (WPML, Polylang): one draft per language, linked by the owner, unless the plugin's API is exposed.
- Read back: `GET /wp-json/wp/v2/posts/<id>?context=edit` → `status` is `draft`. Editor link:
  `<baseUrl>/wp-admin/post.php?post=<id>&action=edit`.

### Drupal

- Credential: a user whose role can create the article content type but not publish it (with Content Moderation:
  can create drafts only), through basic auth (core `basic_auth` module) or an OAuth token (`simple_oauth`).
- Create (JSON:API module): `POST <baseUrl>/jsonapi/node/<options.bundle, default article>`, headers
  `Content-Type: application/vnd.api+json`, body `{data: {type: "node--article", attributes: {title,
  body: {value: <HTML>, format: <options.format, default basic_html>}, status: false, path: {alias: "/<slug>"},
  moderation_state: "draft"}}}` (`moderation_state` only with Content Moderation). Translations: one request per
  language with the `langcode` attribute when the site's translation setup allows it.
- Read back the node: `status` false. Editor link: `<baseUrl>/node/<nid>/edit`.

### Contentful

- Credential: a personal access token of a user whose role can edit but not publish the blog's content type
  (Settings → Roles), or a CMA token the owner restricts the same way.
- `options`: `space`, `environment` (default `master`), `contentType` (the blog post type id), `locales` (site
  language → Contentful locale, e.g. `{"fr": "fr-FR"}`), `fields` (title, slug, body, description, date field ids).
- Create: `POST https://api.contentful.com/spaces/<space>/environments/<env>/entries`, headers
  `Authorization: Bearer …`, `Content-Type: application/vnd.contentful.management.v1+json`,
  `X-Contentful-Content-Type: <contentType>`, body `{fields: {<field>: {<locale>: value}}}`. A new entry is a draft
  until someone publishes it: never call the publish endpoint. A Rich Text body needs Contentful's rich-text JSON
  (convert headings, paragraphs, lists and links); a long-text field takes Markdown.
- Read back: `sys.publishedVersion` absent. Editor link:
  `https://app.contentful.com/spaces/<space>/entries/<id>`.

### Strapi

- Credential: an **API token** of a custom type with only `create`, `find` and `findOne` (and `update`) on the
  article collection (Settings → API Tokens). Draft & Publish must be on for the collection.
- Strapi 5: `POST <baseUrl>/api/<options.collection, default articles>?status=draft`, body `{data: {...fields}}`.
  Strapi 4: `POST <baseUrl>/api/<collection>`, body `{data: {...fields, publishedAt: null}}`. Field names come from
  the collection (`options.fields`); a `blocks` field (Strapi 5 rich text) needs Strapi's blocks JSON, a `richtext`
  field takes Markdown. Locales: `locale` field or `?locale=` with the i18n plugin.
- Read back: `publishedAt` null (Strapi 4) or the document absent from `?status=published` (Strapi 5).

### Webflow

- Credential: a **site token** with CMS read and write scope (Site settings → Apps & integrations).
- `options`: `collectionId` (the blog collection), `fields` (Webflow field slugs for body, summary, date, image…).
- Create: `POST https://api.webflow.com/v2/collections/<collectionId>/items`, body `{isDraft: true,
  isArchived: false, fieldData: {name: <title>, slug, <body field>: <HTML>, …}}`. Never call the publish endpoints.
  Localized sites: `cmsLocaleId` per locale.
- Read back: `isDraft` true. The owner reviews in the Webflow Designer or Editor, then publishes the item.

### Ghost

- Credential: an **Admin API key** of a custom integration (Settings → Integrations). It can publish: the agent
  only ever sends `status: "draft"`. The key is `id:secret`; each request is signed with a short-lived JWT
  (HS256, header `kid` = id, payload `aud: "/admin/"`, `iat`, `exp` within 5 minutes).
- Create: `POST <baseUrl>/ghost/api/admin/posts/?source=html`, header `Authorization: Ghost <jwt>`, body
  `{posts: [{title, slug, html, custom_excerpt, meta_title, meta_description, tags: [{name}], status: "draft"}]}`.
- Read back: `status` draft. Editor link: `<baseUrl>/ghost/#/editor/post/<id>`.

### `custom` (a back office with its own API)

The profile describes the API: `options.list` (endpoint listing articles, to avoid duplicates), `options.create`
(endpoint creating a draft), `options.update` (editing a draft), `options.auth` (`bearer` or `header:<name>`),
`options.fields` (how title, slug, description, body, languages, category and tags map to the API's JSON),
`options.bodyFormat` (`markdown` or `html`). Use only those endpoints. Example, SkillzForest:

```json
"cms": {
  "type": "custom",
  "baseUrl": "https://<api host>/api/v1",
  "tokenEnv": "SKILLZFOREST_ADMIN_TOKEN",
  "options": {
    "auth": "bearer",
    "list": "GET /agent/articles",
    "create": "POST /agent/articles",
    "update": "PATCH /agent/articles/{id}",
    "bodyFormat": "markdown",
    "fields": {"slug": "slug", "title": "title.{lang}", "description": "description.{lang}",
               "body": "body.{lang}", "section": "learn", "category": "guides", "tags": "tags"}
  }
}
```

### Other platforms

Wix, Squarespace, Shopify, HubSpot, Sanity, Prismic, Joomla, Typo3…: use `markdown` unless the owner provides an
API credential limited to drafts and the API can create an unpublished post (Shopify Admin API: `published: false`;
HubSpot CMS blog posts: created as drafts; Sanity: a `drafts.` document id) — then describe it as `custom`.

## `markdown`

`content.markdown`: `dir` (default `<paths.reports>articles/`), `html` (default true: an HTML twin for editors
that take HTML, such as WordPress's code editor or Webflow's rich text). One folder per article and language
(`SKILL.md`, step 5). Validation lives on the ticket:

1. The agent moves the ticket to **To review** with links to the files.
2. The owner reads, then either moves it to **Approved**, or asks for changes in a comment and adds the label
   `article:changes` (sheet: status `Changes`): the next run revises that article only (`SKILL.md`, step 1).
3. The owner pastes it into the CMS and publishes, then moves the ticket to **Published** with the article's URL —
   or simply publishes: the next run finds the URL live (the slug on the site) and closes the ticket.

# Channel map

A project is made known through **communication** channels and put in the users' hands through **distribution**
channels. The map lists both families, every channel inside them, and the places inside each channel where an action
can happen. It is detected for each project, never copied from another one.

## Families and channel types

| Family | Group | Channel types (examples) |
|---|---|---|
| Communication | Owned | site and blog (SEO skills), product changelog and release notes, documentation, newsletter, demo videos on the site |
| Communication | Social | LinkedIn, X, Bluesky or Mastodon, YouTube, TikTok, Instagram, Reddit as a publisher |
| Communication | Community | forums, Discord and Slack servers, GitHub discussions, Q&A sites, Reddit as a member |
| Communication | Earned | trade press and sections, podcasts, newsletters of others, creators and reviewers, comparison articles, awards |
| Communication | Events | trade shows (visit or stand), meetups, talks, webinars, hackathons |
| Communication | Paid | search ads, social ads, newsletter sponsoring, sponsored content (always « à valider », never launched without a cost decision) |
| Distribution | Marketplaces and stores | plugin and app stores (WordPress.org, Shopify App Store, PrestaShop Addons), simulator file libraries, extension stores |
| Distribution | Registries | package registries (npm, PyPI, Packagist), MCP and agent registries, container registries, GitHub releases |
| Distribution | Directories and comparators | software directories (SaaSHub, Product Hunt, G2, Capterra, AlternativeTo, national directories), « awesome » lists |
| Distribution | Integrations and partners | platform partner programs, agencies and integrators, resellers, publishers that bundle, technology partners |
| Distribution | Direct sales | B2B email, demos, trials, sales at events |
| Distribution | Product-led | free tier or licence, « powered by » mentions, referral, templates and examples others reuse |

## Places inside a channel

A channel is too wide to act on. List its **places**: the exact spots where an action happens, each with its
link. Examples: Reddit → r/Xplane (Video flair posts, Help Request answers); WordPress.org → plugin listing, support
forum of the plugin, « Plugins » showcase tags; trade press → the section and the outlet's news form; a forum →
its showcase subforum and its help subforums.

For each place note: the persona present (source), the format that works there, the self-promotion rules (link, read
this run), the account needed and its status (`channels.accounts`), whether automation is allowed (terms link, else
« manuel »), and what can be measured there (clicks with UTM, downloads, installs, replies, coverage).

## Detection

For each project, in this order:

1. The profile: `channels.candidates`, the audiences' `where`, `assets`, `partners`, `media`.
2. The product itself: what it plugs into (platforms, simulators, CMS, APIs) points to its stores, registries and
   partner programs; what it replaces points to comparison pages and directories.
3. The intelligence files of the last four weeks: places where competitors or the audience were seen.
4. Competitors: where each one is listed, reviewed, discussed or sold (their sites' « integrations », « press »,
   « download » pages, and searches on the competitor's name).
5. Searches for the problem the product solves, in the audience's words and languages: the places that rank or
   answer are channels.

Keep a place only when it was read during the run (link and date). A place that could not be read is « non vérifié »
and cannot score more than 5 on reach.

## File `strategy/channel-map.md`

```markdown
# Carte des canaux <Projet> · <date>

## Communication
### <Groupe> · <Canal> · score <n> · verdict <verdict>
| Emplacement | Persona (source) | Format | Règles (lien) | Compte | Automatisation | Mesurable |
|---|---|---|---|---|---|---|
Actions retenues : <ids des actions, avec leur score>

## Distribution
(same layout)

## Écartés
<channel or place> · reason
```

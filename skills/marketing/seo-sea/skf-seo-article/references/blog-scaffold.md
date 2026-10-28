# Creating the blog section (mode `repo`)

When the site has no blog, the first article ticket (`type: setup`) adds one, in a pull request of its own, built
the way the site already builds its pages. Never add a framework, a CMS or a dependency the site does not use
unless nothing else can work, and then say so in the pull request.

## 1. Read the site

- Framework and how a page is made: `astro.config.*` (Astro, content collections in `src/content/`),
  `next.config.*` (Next.js: `app/` or `pages/`, static export or not), `nuxt.config.*`, `gatsby-config.*`,
  `hugo.toml`/`config.toml` (Hugo, `content/`), `_config.yml` (Jekyll, `_posts/`), `.eleventy.js` (Eleventy),
  `docusaurus.config.*` (Docusaurus has a blog plugin), `svelte.config.*`, plain HTML.
- An existing page to copy: its layout, header, footer, metadata helper (title, description, canonical, Open
  Graph), styles.
- How the sitemap is built (generated, a file, a plugin), the robots rules, the checks (`repo.check`, SEO scripts
  that list pages), the navigation and footer.
- The languages (`languages.list`) and how routes are localized.

## 2. Build

Prefer the framework's native content mechanism: Astro content collections, Hugo or Jekyll posts, Docusaurus
blog, Eleventy collections, MDX or Markdown files with Next.js or Nuxt content, or — when the site has none — one
data file per article (JSON or Markdown) read at build time. Add:

1. **Article storage**: a folder per language when the site is multilingual, one file per article; the format and
   its required fields written down for the agent.
2. **Blog index** (`/blog/`, or the site's word for it per language): newest first, title, date, excerpt, reading
   time, link; its own title and description.
3. **Article page**: the layout of the site's pages, one H1 (the title), date, reading time, the body (headings,
   paragraphs, lists, links, images), a « Sources » section, two or three related articles, `BlogPosting` JSON-LD
   (headline, description, datePublished, dateModified, inLanguage, author, publisher, mainEntityOfPage),
   canonical, Open Graph type `article`, `hreflang` between translations.
4. **Sitemap**: the index and every article, with its date as `lastmod`, generated from the article files.
5. **Navigation**: a « Blog » link in the footer (and the header when it has room).
6. **Checks**: extend the site's SEO checks and tests so they cover the blog pages (titles, descriptions, unique
   titles, links); add one test that every article file has the required fields.

Build once with a temporary example article to see the pages, then remove it: the pull request ships the section
empty or with the plan's first article only if the owner asked for both at once.

## 3. Record it

Fill `repo.blog` in `.seo/profile.json` in the same pull request (`dir`, `format` with every required field and
the title limit after the layout's suffix, `urlPattern`, `images`, `rules`), and `content.publish: "repo"`.
`repo.check` must pass. The pull request body: what was added, how to add an article (one file), the screenshots
or URLs to look at, and that articles start once it is merged.

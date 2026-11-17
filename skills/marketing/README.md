# skills/marketing — Marketing & Growth

The site's **Marketing & Growth** category (pros & teams). Its subcategories are `content/`, `seo-sea/`, `social-media/` and `emailing/` (see [`skills/domains.json`](../domains.json)); `content/`, `seo-sea/` and `social-media/` hold skills today.

## `content/`

- `skf-masters-kit-presse` — reads a website's brand (colors, fonts, logos, tone), then builds two reusable press-kit masters for a digital product launch: a 16:9 deck (Google Slides or .pptx) and a document (Google Docs or .docx) with a press release, a creators brief and a Q&A, all with `{{FIELD}}` placeholders. See its [`README.md`](./content/skf-masters-kit-presse/README.md).

## `social-media/` — Shorts Factory

Three skills used in order (pack [`shorts-factory`](../../packs/marketing/social-media/shorts-factory/pack.json), workflow [`shorts-factory`](../../workflows/shorts-factory/WORKFLOW.md)) to turn an idea or a SaaS into a short video for YouTube Shorts, TikTok, Instagram Reels, X and Bluesky. Everything lives in `shorts/<slug>/` of the working directory.

- `skf-shorts-sources` — asks the networks, the idea, the call to action and the sources (website, documents, cloud folders, videos, sounds); reads the site's brand and screenshots, inventories media, extracts sourced facts → `kit.json`.
- `skf-shorts-studio` — angle, hook and script screen by screen (validated), then a Remotion render: 9:16 video (+ 4:5), covers 9:16 / 4:5 / 1:1 / 16:9 in the brand's look, checks per network, frames to review → `storyboard.json`, `out/`.
- `skf-shorts-publish` — one caption per network, validated, then publish / schedule / draft through Postiz, or a manual upload kit → `publish.json`, `publish-log.json`.

Python scripts use the standard library only (Pillow, when installed, adds a contact sheet). Rendering needs Node.js and a Remotion project (`render_short.py --scaffold` installs one in `~/.skf-shorts/remotion`); Chrome, Chromium or Edge takes the site screenshots.

# Campaign folder (`projects/<id>/campaigns/YYYY-MM-DD-slug/`)

```text
brief.md            objective, audience, persona, message, proof points (with sources), channels, dates, metric, stop criterion
messages.md         the master message and its variants per audience (2 or 3 when testing an angle)
posts/<channel>.md  one file per channel: the text ready to paste, length checked, link with UTM, visual reference, posting slot
video/script.md     when a video is planned: hook, scenes with timing, voice-over, on-screen text, call to action, captions file name
video/storyboard.md one row per scene: duration, what is shown (real screen capture, never a fake UI), text, sound
visuals.md          what each visual must show, its sizes per channel, the tool to make it, alt text
press/release.md    when press is targeted: headline, lead, body, quote from the owner (marked « à valider »), boilerplate, contact placeholder
press/kit.md        fact sheet, screenshots list, links, logos list, owner bio placeholder
calendar.md         Date · Channel · Asset · Status (draft, approved, published) · Published URL
```

Rules for every text:

- The product facts come from the growth profile, the SEO profile and the files they name. No feature, figure,
  compatibility, customer or quote that is not there.
- The SEO profile's `style.rules` and the growth profile's `constraints` apply (brand spelling, words to avoid).
- Each post fits its platform's current limits (read on the platform's help page during the run when unsure).
- Links carry UTM parameters: `utm_source=<channel>&utm_medium=<social|email|press|community>&utm_campaign=<slug>`.
- A post for a community follows that community's self-promotion rules (link in `brief.md`); when the rules forbid
  it, there is no post for that place.
- The owner's quote in a press release is a proposal marked « à valider »; never attribute words to anyone else.
- Video: real product footage only; music and images free of rights with their licence named in `visuals.md`.

UTM and slugs: lower case, no accents, hyphens.

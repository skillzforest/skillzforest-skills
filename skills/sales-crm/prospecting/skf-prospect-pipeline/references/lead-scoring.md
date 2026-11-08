# Lead scoring and pipeline files

## Kinds

| Kind | What it is | Typical next step |
|---|---|---|
| `client` | an organization that could buy or use the product | demo or trial proposal |
| `partner` | an organization that could distribute, integrate or bundle it (agency, integrator, platform, maker) | partnership proposal |
| `prescriber` | an organization whose advice the audience follows (association, school, consultant, community) | presentation, content collaboration |
| `media` | an outlet or a section that covers the topic | story pitch, test, interview |

Creators and influencers are followed by the creator outreach skill when the project has a social profile; here they
appear only as organizations (a media company, a channel's business entity).

## Score out of 100

| Criterion | Points | 0 | Max |
|---|---|---|---|
| Fit with the ICP or the partner kind | 30 | outside every industry, size or geography of the profile | matches industry, size, geography and has the role the profile targets |
| Need or interest signal | 25 | no signal | a dated public signal from the last 90 days (job ad, announcement, migration, article, question) |
| Potential | 20 | no plausible value | a deal, a distribution channel or an audience that moves a goal |
| Feasibility | 15 | no legitimate way to reach the right person | a public professional contact route (contact page, press page, partner program) |
| Confidence in the data | 10 | single weak source | two sources, one of them the organization's own |

Classes: **A** 70 and more (propose this week), **B** 50 to 69 (propose when the A list is short), **C** under 50
(keep in the pipeline file, no action). A disqualifier of the ICP sets the score to 0.

## Weekly pipeline file (`projects/<id>/pipeline/YYYY-Www.md`)

```markdown
# Pipeline <Project> · semaine YYYY-Www

| Organisation | Domaine | Nature | Score | Classe | Signal (date, lien) | Voie de contact | Fiche CRM | Issue |
|---|---|---|---|---|---|---|---|---|

## Écartés
Organisation · raison (disqualifiant, doublon, opposition enregistrée)
```

Organizations only. The person to contact, with role and professional address, lives in the CRM record; the file
links to it.

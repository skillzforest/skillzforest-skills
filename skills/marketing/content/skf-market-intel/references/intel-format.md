# Weekly intelligence file (`projects/<id>/intel/YYYY-Www.md`)

Written in the profile's `reportLanguage`. One file per project and ISO week; a second run in the same week appends a
dated section instead of overwriting.

```markdown
# Veille <Project> · semaine YYYY-Www

Période couverte : YYYY-MM-DD → YYYY-MM-DD · sources lues : N · éléments retenus : N

## En bref
Three lines at most: what changed for this project this week, and the one thing worth acting on.

## Marché et tendances
| Fait | Source | Publié | Lu | Confiance |
|---|---|---|---|---|

## Concurrents
| Concurrent | Ce qui a changé | Source | Publié | Confiance |
|---|---|---|---|---|

## Audiences et besoins exprimés
Questions, complaints and requests people wrote in public, quoted in under 15 words or paraphrased, with the link.

## Médias, journalistes et créateurs
| Média ou créateur | Sujet couvert récemment | Pourquoi pour nous | Lien | Confiance |
|---|---|---|---|---|
Outlets, sections and public professional handles only; no personal email or phone.

## Communautés et plateformes
| Lieu | Taille ou activité observée | Règles d'autopromotion lues | Lien |
|---|---|---|---|

## Partenaires et entreprises (signaux)
| Organisation | Signal (besoin, annonce, recrutement, lancement) | Nature (client, partenaire, prescripteur) | Source | Confiance |
|---|---|---|---|---|

## Événements et calendriers éditoriaux
| Événement | Date | Lieu ou format | Échéance utile (appel à sujets, inscription) | Source |
|---|---|---|---|---|

## Opportunités proposées
One line per opportunity sent to the tracker: growth-id, title, why now, link to the issue.

## Hypothèses
What this week suggests but no source confirms.

## Non trouvé ou non vérifié
What was searched and not found, sources that refused access, claims left out for lack of a source.
```

Rules:

- A fact older than 12 months is kept only when nothing newer exists, and its row says so.
- « Publié » is the publication date shown by the source; « Lu » is the date of this run.
- Confidence: `haute` (the organization's own page, an official text), `moyenne` (reputable outlet), `faible`
  (a single post, a listing, an undated page).
- Quotes from a source: one per source at most, under 15 words; paraphrase everything else.

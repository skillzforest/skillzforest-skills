# Growth reports and measures

## Weekly measures (`projects/<id>/metrics/YYYY-Www.json`)

```json
{
  "project": "romkade",
  "week": "2026-W45",
  "window": { "from": "2026-11-02", "to": "2026-11-08", "timezone": "Europe/Paris" },
  "metrics": [
    { "id": "visitors", "family": "acquisition", "value": 412, "previous": 380, "source": "PostHog project 312170, $pageview uniq person", "read": "2026-11-09" },
    { "id": "search-impressions-28d", "family": "awareness", "value": null, "source": "Search Console sc-domain:romkade.com", "note": "non mesuré : propriété sans données" }
  ],
  "pipeline": { "qualified": 0, "proposed": 0, "approved": 0, "sent": 0, "replies": 0, "conversations": 0, "meetings": 0, "opportunities": 0 },
  "operations": { "decisionsAsked": 0, "decisionsAnswered": 0, "approved": 0, "experimentsRunning": 0, "experimentsConcluded": 0, "ownerMinutesEstimate": null },
  "byChannel": [ { "channel": "bluesky", "posts": 0, "clicks": null, "signups": null } ]
}
```

Families: `awareness` (organic discovery, mentions, channel visibility, brand searches, press coverage),
`acquisition` (qualified visits, sign-ups, downloads, installs, activations), `bizdev` (the pipeline block),
`operations`. A value that no source gave is `null` with a `note`; never an estimate. A week whose volumes are under
20 visitors says « volume trop faible pour conclure ».

## Daily point (`reports/daily/YYYY-MM-DD.md`, and the tracker item « Point du jour »)

Three lines at most:

```text
Décisions en attente : N (dont P1 : N) · <lien vue cockpit>
Demain : <échéances, publications prévues, relances dues>
Alerte : <une seule, ou « rien »>
```

## Weekly review (`reports/weekly/YYYY-Www.md` and a page for the owner)

1. **En une minute**: three lines on the week across projects.
2. **Décisions à prendre**: one block per decision waiting, most valuable first: project, opportunity, channel or
   target, expected outcome, rationale, sources, effort, confidence, risks, recommendation, link. The owner answers on
   the issue.
3. **Par projet**: KPI table (value, previous, change, source), what moved and why (facts), what was done, what is
   prepared, the next step.
4. **Expériences**: running, concluded (result against the stop criterion), next.
5. **Arbitrages proposés**: where the owner's time and any budget should go next week, between projects, with the
   reason.
6. **Données manquantes**: metrics not measured and what would make them measurable.
7. **Coût**: model usage when the workspace has a usage file, the owner's time estimate when items carry Effort.

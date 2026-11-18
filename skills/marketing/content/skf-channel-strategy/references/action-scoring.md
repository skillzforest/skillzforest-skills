# Actions: scoring, tracking and impact

Inside every channel scored **test**, **launch** or **strengthen**, list the concrete actions possible on its places,
score them, keep the best ones, and make each one measurable before it starts.

## What an action is

One thing done once or on a short cadence, on one place, with one message, that can be measured: « publier une
vidéo démo de 60 s dans r/Xplane avec le flair Video », « soumettre la fiche du plugin à WordPress.org », « proposer
un sujet à la rubrique Retail du JDN ». « Faire du LinkedIn » is a channel, not an action.

Action types: `publish` (post, video, article), `list` (store, registry or directory listing), `pitch` (press,
creator, podcast), `answer` (useful replies in a community), `event` (visit, talk, stand), `partner` (partner
program, integration), `outreach` (B2B message), `release` (announcement tied to a version), `paid` (always « à
valider »).

## Action score out of 100

| Criterion | Points | 0 | Max |
|---|---|---|---|
| Impact on a goal | 35 | no path to a goal metric | direct effect on a 30 d goal metric (downloads, sign-ups, demos) |
| Evidence | 20 | pure guess | a measured result of the same kind for this project, or a sourced case on the same place |
| Timing | 15 | no reason to act now | a dated window (release, event, launch, editorial calendar) in the next 30 days |
| Owner effort (inverse) | 15 | more than half a day of the owner | under 30 min of the owner, the rest prepared by the agent |
| Reuse | 10 | everything to create | built from existing assets (merged articles, guides, videos, demos) |
| Measurability | 5 | impact cannot be told apart | own UTM, own event or own counter |

Keep at most **3 actions per channel** and **10 per project** at a time, best scores first. An action that is
public or binding (post, listing, pitch, account, spend) goes to the owner as a decision.

## Tracking before launch

An action starts only when its measurement is ready, or it is labeled « non mesurable » with the reason:

- links carry `utm_source=<channel>&utm_medium=<medium>&utm_campaign=<action slug>&utm_content=<place>`;
- the analytics tool sees the landing (PostHog: `$pageview` with `utm_campaign` set) and, when it exists, the goal
  event (sign-up, download click, licence request, first API call);
- stores, registries and directories: their own counters (installs, downloads, listing views) read on their public
  or owner pages;
- earned and community actions: the published URL, its referrals in analytics, the replies.

A goal event missing from the analytics is a measurement gap: say it in the strategy file and propose its
instrumentation as an item (Nature Opportunity) once, not every week.

## Action record (`strategy/actions.json`)

```json
{
  "project": "xp-flightdeck",
  "updated": "2026-11-18",
  "actions": [
    {
      "id": "channel:xp-flightdeck:reddit-xplane-video-demo",
      "family": "communication",
      "group": "community",
      "channel": "reddit",
      "place": "r/Xplane, flair Video",
      "type": "publish",
      "title": "Vidéo démo de 60 s : la tablette pilote feux, volets et freins",
      "score": 71,
      "scoreDetail": { "impact": 25, "evidence": 8, "timing": 10, "effort": 12, "reuse": 8, "measurability": 5 },
      "goal": "downloads-30d",
      "hypothesis": "Une démo courte amène des visiteurs qualifiés vers la page de téléchargement",
      "tracking": { "utm_campaign": "reddit-xplane-video-demo", "event": null, "other": "votes et commentaires du post" },
      "window": { "days": 14, "metric": "visiteurs avec utm_campaign, clics vers le téléchargement", "success": ">= 30 visiteurs", "stop": "< 10 visiteurs" },
      "issue": 32,
      "status": "proposed",
      "launched": null,
      "baseline": null,
      "result": null,
      "verdict": null
    }
  ]
}
```

`status`: `proposed` → `approved` → `running` (launch date set) → `measured` (window over, result written) or
`dropped`. `verdict` after measurement: `works` (success threshold met), `neutral`, `fails` (stop criterion hit),
`insufficient-data` (volume under 20 visitors or no tracking). The id is the tracker growth-id when the action has an
item; an existing item that already describes the action is linked, never duplicated.

## Impact back into the channels

- A channel's measured signal bonus (scoring grid) comes from the verdicts of its actions over the last three months:
  each `works` +5, each `fails` -5, capped at ±15; `insufficient-data` counts 0.
- Two `fails` in a row on the same place: the place is dropped for 90 days.
- A `works` action becomes a cadence in the 90 day plan.

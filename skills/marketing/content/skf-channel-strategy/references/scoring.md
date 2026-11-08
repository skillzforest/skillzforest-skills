# Channel scoring grid

Score each candidate channel of a project out of 100, always with the same grid, so that months can be compared.

| Criterion | Points | 0 | Max |
|---|---|---|---|
| Audience reach | 25 | the profile's audiences are not there | a sourced place where a core persona gathers and is active this month |
| Fit | 20 | the product's message does not fit the format or the culture | the format shows what the product does (a demo for a tool, a guide for a search need) |
| Potential impact on a goal | 20 | no link to any goal | a direct path to a 30 d or 90 d goal metric |
| Owner effort (inverse) | 15 | more than a day a week | under an hour a week, mostly prepared by the agent |
| Cost (inverse) | 10 | paid placement or paid tool needed | free with existing tools and accounts |
| Constraints (inverse) | 10 | terms forbid what we would do, or self-promotion is banned | rules read and compatible with an honest presence |

Add a **measured signal** bonus or malus from the previous months, between -15 and +15, only from measured results
(clicks, sign-ups, replies, coverage) attributed to the channel in `metrics/`. No data: 0, and say so.

Verdict, by score and evidence:

| Score | Verdict | Meaning |
|---|---|---|
| 70 and more | **launch** or **strengthen** | worth a regular cadence |
| 50 to 69 | **test** | one bounded experiment with a stop criterion |
| 30 to 49 | **watch** | keep an eye on it, no action |
| under 30 | **drop** | not for this project now, reason written |

A channel already running whose experiments failed their stop criterion twice is **reduced** or **dropped**,
whatever its score.

Every experiment has: hypothesis, action, duration (2 to 4 weeks), metric with its source, success threshold, stop
criterion, owner time needed, cost.

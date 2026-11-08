---
name: skf-campaign-studio
description: Turns approved opportunities of the growth workspace into ready-to-use campaigns for one project, then organizes their distribution - reuses merged SEO articles, guides, demos and videos, writes the campaign brief, the master message and its variants per audience, posts per channel (or hands them to skf-social-compose when the Social Factory is installed), short video scripts and storyboards, visual briefs, press releases and press kits, and a publication calendar with UTM links. In distribution mode it checks which assets are approved and ready, avoids duplicate or repetitive posts, prepares the manual publication pack or the scheduled post, and records the published URLs. Nothing is published without the owner's explicit approval. Use it when an opportunity is approved, for the weekly campaign preparation, or whenever someone asks for posts, a video script, a press release, a press kit or a publication calendar for a project.
---

# Campaign studio

You prepare what the owner will publish or send, so that publishing takes minutes. Read first:
`../skf-growth-profile/references/guardrails.md`, the project's `growth.json`, its SEO profile, `strategy/channels.md`
and `strategy/plan-30d.md`, and the decision log. Folder format:
[`references/campaign-format.md`](references/campaign-format.md).

The profile must be `validated`; otherwise prepare nothing and say so.

## Mode prepare (default)

1. **Pick the work.** Items of the project on the tracker with Status Approved and Nature Opportunity, Campaign,
   Content or Publication, oldest due first; an item in Status In preparation whose last owner comment is a CHANGE
   note comes first (the note is the brief). At most two campaigns per run.
2. **Gather material.** Merged articles and guides of the site (the SEO profile's `repo.blog`, only merged ones),
   the project's `assets`, previous campaigns (do not repeat an angle used in the last 30 days on the same channel),
   the intelligence file that produced the opportunity.
3. **Write the brief** (`brief.md`): one objective tied to a goal of the profile, one persona, one message, three
   proof points with their source, the channels from `channels.md` with verdict launch, strengthen or test, dates,
   metric and stop criterion.
4. **Write the assets** the brief needs, and only those: messages and variants, posts per channel, video script and
   storyboard, visual briefs, press release and kit. When the Social Factory skill `skf-social-compose` is installed
   and the project has a social profile (`channels.socialProfile`), give it the master message and let it write the
   per-channel posts in its own format; link its output from `calendar.md`.
5. **Check** every text against the facts and rules (format file), every length, every link.
6. **Deliver.** Commit the folder on a branch `growth/campaign-<id>-<slug>`, open a pull request in the workspace.
   Through `skf-growth-tracker` (mode log): the campaign item moves to Status Decision with label `decision:pending`
   and Deliverable link = the pull request; one Publication item per planned post or send (Status Decision, Due =
   planned date, Channel set) so the owner can approve each one on the publication calendar view.

## Mode distribute

1. Items with Nature Publication in Status Approved whose Due is today or past, and items Ready.
2. For each: check that the asset exists in a merged campaign folder, that nothing with the same text was published on
   that channel in the last 30 days (`calendar.md` of every campaign of the project), and that the channel's account
   is `active`.
3. Prepare it:
   - a scheduling tool connected and allowed for that channel (for example Postiz through `skf-social-publish`):
     schedule it only when the item was approved as a publication, and report the scheduled time;
   - otherwise a **manual pack**: the exact text, the visual file, the link, where to click, in a comment on the
     item; Status Ready, label `needs:owner`.
4. When the owner reports the publication (comment « publié » / "published" with the URL, or the scheduler's
   confirmation), write the URL in `calendar.md` and the Deliverable link; Status Done.

## Guardrails

- No publication, comment, reply, message or account creation without an approved item for exactly that action.
- Never post the same text twice on one channel, never more than the frequency of `channels.md`.
- No invented testimonial, review, figure or quote.

## Final answer

In `reportLanguage`: campaigns prepared (pull request links), publications waiting for approval, manual packs ready,
URLs recorded, and what was skipped and why.

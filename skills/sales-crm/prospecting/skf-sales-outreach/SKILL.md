---
name: skf-sales-outreach
description: Prepares the contact with organizations the owner approved in the growth workspace - chooses the right route and offer per prospect, partner, prescriber or media outlet, writes one personalized first message that proves it looked at their real signal, a demo or partnership proposal, and the single follow-up; reads the replies it can access, summarizes them, drafts the answer, updates the CRM, records refusals and opt-outs for good, and flags what needs the owner. Never sends anything itself unless the owner approved that exact message, never mass mailing, never cold messages to private individuals. Use it after a prospect or media item is approved, for the weekly follow-up of open conversations, or whenever someone asks to write a sales email, a partnership request, a press pitch, a follow-up or an answer to a prospect.
---

# Sales outreach

You write the messages the owner will be glad to sign. Read first:
`../../../marketing/content/skf-growth-profile/references/guardrails.md`, the project's `growth.json` (`outreach`,
constraints) and SEO profile (facts, style rules), and the guide
[`references/outreach-guide.md`](references/outreach-guide.md).

The profile must be `validated`.

## Mode draft (default)

1. **Work list.** Tracker items of the project with Nature Prospect or Media/Partner in Status Approved (or In
   preparation with a CHANGE note), oldest first, at most `outreach.maxFirstMessagesPerWeek` minus the first messages
   already proposed this week.
2. **For each**: open the CRM record (contact, role, route, source), reread the signal on its page (still there, still
   current), choose the route and the offer (guide), write the message and, separately, its follow-up.
3. **Check**: every fact about the organization has its source; every product fact is in the profile; the « another
   organization » test passes; opt-out line present for EU B2B email.
4. **Store**:
   - in the workspace, `outreach/YYYY-MM-DD-<domain>.md`: organization, route, offer, the message with the greeting
     written as `{prénom}` / `{first name}`, the follow-up, the sources; no address, no phone;
   - in the CRM, a note on the contact with the full personalized message;
   - on the tracker item, through `skf-growth-tracker`: Status Ready, label `decision:pending`, Deliverable link = the
     workspace file, and a comment asking for the second approval: « APPROUVER pour envoi » / "APPROVE to send".
5. **After approval to send**: with `outreach.sender.channel: gmail` and a connected mailbox, create a draft in that
   mailbox (never send it) and tell the owner it waits in Drafts; with `manual` or `null`, the text ready to paste and
   the route are in the item comment, label `needs:owner`. The owner sends. When the owner says it is sent, log the
   date in the CRM and set Status Done; plan the follow-up date (Due + 7 to 10 days) on the item.

## Mode follow-up

1. Items Done with an outreach message and no reply, whose follow-up date has come: propose the follow-up exactly as a
   first message (second approval, draft, the owner sends). After it, no third message: close as « sans réponse » at
   the next run once 14 days have passed.
2. Replies: when a mailbox tool is connected, search the threads of the sent messages (by subject and recipient
   domain, read only). For each reply: one-line summary, proposed answer, decisions that belong to the owner (price,
   terms, dates, commitments). A refusal or an opt-out: record the opposition on the CRM contact, close the item as
   REJECT with the reason « refus du destinataire », never contact again.
3. Report the conversations that need the owner (a meeting to accept, a question on price) as items with label
   `needs:owner`.

## Guardrails

- One message per approval, one approval per message: an approval of one message never covers another.
- Never send directly, never schedule a send, never write from a mailbox the profile does not name.
- No private individuals, no bulk sends, no purchased lists, no tracking pixels.
- Never answer on price, terms or commitments: prepare, flag, wait.

## Final answer

In `reportLanguage`: messages ready for approval (item links), drafts placed in the mailbox, follow-ups due, replies
received and what they need, contacts closed.

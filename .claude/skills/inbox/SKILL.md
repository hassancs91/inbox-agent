---
name: inbox
description: Read the inbox, sort every email, and draft replies for the ones that need an answer. Never sends, never deletes. Use when the user runs /inbox.
---

# The inbox agent

You are my inbox assistant. One run reads the new emails, reads what they mean to me,
decides what each one is, labels it, and writes reply drafts for the ones that need an
answer. Then it tells me what it did.

## The rule

You draft, I send. You sort, you never delete.

There is no tool in this folder that can send an email or delete one, and you never ask
for one.

## Steps

1. Fetch the emails: `uv run tools/fetch.py`. It writes them to `work/inbox.json`.
   If it says Gmail is not connected, run `uv run tools/fetch.py --sample` instead, and
   use `--sample` on every later tool in this run.
2. Read `work/inbox.json`. Every email in it gets a decision.
3. Read every file in `context/`. That is what these emails mean to me:
   - `about-me.md` says whose inbox this is and what I do.
   - `categories.md` says what each of the five categories means for me, with examples
     from my life.
   - `sender-rules.md` names senders whose mail always gets the same category.
   A file that still says *Not filled in yet* is a template and adds nothing.
4. Decide a category for each email. Exactly one of these five, spelled exactly like this:
   - `needs-reply` — a person wrote to me and expects an answer from me
   - `urgent` — the same, and the email names a deadline falling today or this week
   - `newsletter` — a mailing I subscribed to; nobody is waiting for a reply
   - `notification` — a system telling me something happened (a repo, a calendar, a service)
   - `other` — anything that fits none of the above
   When both `needs-reply` and `urgent` fit, `urgent` wins.
   My context refines these five. It never adds a sixth or renames one. Where
   `categories.md` says what a category means for me, that meaning settles what the line
   above leaves open. A sender rule beats your own guess: when the sender's name on the
   email is the name in the rule, or plainly the same person or company, the rule's
   category is the decision, whatever the email says, and the why names the rule.
   Write `work/decisions.json`: a list with one entry per email,
   `{"id": ..., "category": ..., "why": ...}`, the why in one short line.
5. Label them: `uv run tools/label.py` (with `--sample` if step 1 used it). It puts
   `AI/<category>` on each message, one AI label per message, and refuses a category
   that is not in the list.
6. Report, in exactly this shape, and nothing after it:

       Run complete
         fetched 12 · needs-reply N · urgent N · newsletter N · notification N · other N
         labels applied in Gmail · sent 0

   (In sample mode the last line reads `labels recorded in work/labels.json · sent 0`.)
   Then, if anything deserves my eye, at most three plain lines under it. My context
   decides what goes there: what matters most to me first, going by `about-me.md` and
   the rules and examples I gave, each line with its reason. While every file in
   `context/` is still a template, the first line says so and points at `/setup`.

## Done means

Every email in `work/inbox.json` has a decision and a label. Then stop.

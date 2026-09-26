# The inbox agent

This is the project you build in module 2 of **Agentic Automation 3.0**, the course at
[learnwithhasan.com/courses/agentic-automation-3](https://learnwithhasan.com/courses/agentic-automation-3/).
Eight lectures build this folder one piece at a time, with Claude Code, on camera. If you
are not in the course, that page says what it teaches. The folder works on its own too.

An agent that reads your inbox, decides what each email is, labels it, and writes reply
drafts it cannot send.

The rule: **it drafts, you send. It sorts, it never deletes.** That is not a promise in a
prompt. There is no send tool and no delete tool in this folder.

## The shape

The same shape as the setup checker, plus a tools folder:

| | |
|---|---|
| `.claude/skills/inbox/SKILL.md` | the agent: one page of plain English, run by typing `/inbox` |
| `tools/` | Python scripts with one job each and no AI inside, run through `uv` |
| `fixtures/sample-inbox.json` | twelve sample emails, so the agent works before you connect anything |
| `.claude/skills/setup/SKILL.md` | the interview that fills `context/`, run by typing `/setup` |
| `context/` | what the agent reads before it decides: who you are, what the five categories mean to you, which senders have a fixed rule, how you write a reply |
| `memory/` | what it keeps between runs: every email it has handled, and every label you changed by hand |
| `work/` | this run's files, ignored by git |

## Lecture by lecture

Each tag is the folder exactly as that lecture left it. `main` is the finished folder
with an empty memory and template context, ready for your inbox.

| Lecture | Tag | What lands |
|---|---|---|
| 02 The skeleton | `l2-skeleton` | the folder, the skill, `fetch.py`, twelve sample emails |
| 03 Connect Gmail | `l3-connected` | one permission, `connect.py`, `/connect-gmail` |
| 04 The first run | `l4-first-run` | five categories, `label.py`, the report |
| 05 Context | `l5-context` | `context/` and `/setup` |
| 06 Drafts, not sends | `l6-drafts` | `voice.md`, `draft.py`, `drafts N · sent 0` |
| 07 Memory | `l7-memory` | `memory/seen.json` and `memory/corrections.md` |

To see the folder as it stood after a lecture:

```
git checkout l4-first-run
```

## Run it

```
git clone https://github.com/hassancs91/inbox-agent
cd inbox-agent
uv run tools/fetch.py --sample
```

That prints `12 in the inbox: 12 new, 0 you changed, 0 already done -> 12 written to
work/inbox.json`. Then open Claude Code in the folder and type `/inbox`. Nothing touches Google until you connect it.

## Teach it what things mean to you

```
/setup
```

Four or five short questions in the chat, one at a time: who you are, what has to reach
you and what makes it urgent, what can wait, whose email always gets the same treatment,
and how you write a reply. Senders are named the way their name shows on the email; it
never asks for an address. The answers become the four files in `context/`, which the
agent reads before it decides. A sender rule beats its own guess. Until you run `/setup`
the files are templates and it decides on its own. Run `/setup` again to see what is there
and change any of it. If the first three are already filled and only `voice.md` is not, it
skips straight to the one question about how you write.

## It drafts, you send

For every email that needs an answer from you, `needs-reply` or `urgent`, the agent writes
the reply in your voice, in the language the sender wrote in, and saves them all to
`work/drafts.json`. It never invents a fact about you: when a reply needs something only
you know, it writes around the gap and tells you under the report what to fill in. Before
saving, it reads each draft back against three checks: it answers what was asked, it is in
the sender's language, and there is no placeholder text.

Then `tools/draft.py` creates a Gmail draft for each one, as a reply inside the same
thread, so it shows up under the email, waiting for you. With `--sample` it records them
in `work/drafts-created.json` instead. A thread that already has a draft is left alone.

The report's last line counts them: `labels applied in Gmail · drafts N · sent 0`. Sent
stays 0, and it stays 0 forever. Nothing in `tools/` can send; the word appears there only
in comments saying so:

```
grep -ri send tools/
```

## It does not do the same work twice

`memory/seen.json` is every email the agent has handled and the label it put on it.
`tools/label.py` writes it the moment the labels are on; `tools/fetch.py` reads it before
it fetches. An email in there, still carrying the label the agent gave it, is done, and
fetch leaves it out. So the second run costs what the new mail costs, and nothing more:

```
12 in the inbox: 3 new, 0 you changed, 9 already done -> 3 written to work/inbox.json
```

Nothing new and nothing changed is the whole run. The agent says so in one line and stops.

## When you correct it, the correction sticks

Change a label in Gmail and you have told the agent it was wrong. The label is no longer
the one it put there, so fetch brings that email back as a correction, saying what the
agent called it and what you call it. The agent writes the correction down in
`memory/corrections.md`, one line, as a rule for every run after this one:

```
[you said] Lina Haddad is `urgent` — 2026-09-15
```

From then on it reads that file along with `context/`, before it decides anything. A line
in it beats what the agent works out for itself, exactly the way a sender rule does; being
the later word, it also beats a sender rule that disagrees. It only ever writes down a
correction you actually made: take a label off without putting another on and you have not
said what the email is, so that one just gets decided again.

With `--sample` there is no Gmail, so the labels the agent compares against are the ones
`label.py` recorded in `work/labels.json`. Edit a label there and the next run sees a
correction, exactly as it would in Gmail.

Both memory files, and `work/labels.json` in sample mode, are updated by a run, never
replaced.

## Connect Gmail

Google asks you once what this program may do. Four steps in Google Cloud, then one
command. The console's labels move around; the shape does not.

1. Create a project at console.cloud.google.com, any name.
2. Enable the **Gmail API** for it (APIs & Services > Library > Gmail API > Enable).
3. Set up the consent screen (APIs & Services > OAuth consent screen, or Google Auth
   Platform > Branding on newer consoles). On a personal Gmail account choose **External**
   and add your own address under **Test users**. On a Google Workspace account choose
   **Internal**.
4. Create an OAuth client of type **Desktop app** (Credentials > Create credentials >
   OAuth client ID), download the JSON, and save it in this folder as `credentials.json`.

Then, in Claude Code:

```
/connect-gmail
```

The browser opens on Google's consent screen. Click Allow. The agent verifies the
connection with one harmless call and tells you what is wrong if a step is red.

The permission is `gmail.modify`. This agent uses it to read, label and draft. It cannot
permanently delete anything: that needs the full-mailbox scope, which is never asked for.
Google's own wording for the permission includes "send"; what stops sending is that no
tool in this folder can send. `credentials.json` and `token.json` stay on your machine
and are ignored by git.

Then fetch for real, same tool, no flag:

```
uv run tools/fetch.py
```

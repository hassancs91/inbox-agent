# The inbox agent

An agent that reads your inbox, decides what each email is, labels it, and writes reply
drafts it cannot send. Built in Agentic Automation 3.0, module 2, one lecture at a time.

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
| `context/` | what the agent reads before it decides: who you are, what the five categories mean to you, which senders have a fixed rule |
| `memory/` | what the agent keeps between runs (filled in lecture 7) |
| `work/` | this run's files, ignored by git |

## Run it

```
git clone https://github.com/hassancs91/inbox-agent
cd inbox-agent
uv run tools/fetch.py --sample
```

That prints `12 emails written to work/inbox.json`. Then open Claude Code in the folder
and type `/inbox`. Nothing touches Google until you connect it.

## Teach it what things mean to you

```
/setup
```

Three or four short questions in the chat, one at a time: who you are, what has to reach
you and what makes it urgent, what can wait, and whose email always gets the same
treatment. Senders are named the way their name shows on the email; it never asks for an
address. The answers become the three files in `context/`, which the agent reads before it
decides. A sender rule beats its own guess. Until you run `/setup` the files are templates
and it decides on its own. Run `/setup` again to see what is there and change any of it.

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

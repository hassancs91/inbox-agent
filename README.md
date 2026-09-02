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
| `context/` | what the agent reads before it decides (filled in lecture 5) |
| `memory/` | what the agent keeps between runs (filled in lecture 7) |
| `work/` | this run's files, ignored by git |

## Run it

```
git clone https://github.com/hassancs91/inbox-agent
cd inbox-agent
uv run tools/fetch.py --sample
```

That prints `12 emails written to work/inbox.json`. Then open Claude Code in the folder
and type `/inbox`.

Nothing here touches Google yet. Connecting Gmail is lecture 3.

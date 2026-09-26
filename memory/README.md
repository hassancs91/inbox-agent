# What the agent keeps between runs

| | |
|---|---|
| `seen.json` | every email it has handled: the id, the category it gave it, and the date of the run. `tools/label.py` writes it, `tools/fetch.py` reads it, and an email in here that still carries the label it was given is one the next run leaves out. |
| `corrections.md` | what you changed by hand after it had decided. One line per correction, written by the agent, and every line beats its own guess on the next run. |

Both are updated by a run, never replaced.

`seen.json` is memory of your inbox, not of this folder. Empty it back to `{}` before you
share the folder, or the next person's first run thinks their mail is already handled.

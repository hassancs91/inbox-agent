---
name: connect-gmail
description: Connect the inbox agent to your Gmail account with one permission, verify it with a harmless call, and explain what is wrong if a step fails. Use when the user runs /connect-gmail or asks to connect Gmail.
---

# Connect Gmail

Connect this folder to the person's Gmail account, then prove it works. Read nothing from
the mailbox here. The only call is the profile call the tool makes.

## What has to exist first

`credentials.json` in this folder: an OAuth client of type **Desktop app** from Google
Cloud, downloaded as JSON. If it is missing, do not try to work around it. Say so, point at
the four steps in `README.md` under *Connect Gmail*, and stop.

## Run the tool

    uv run tools/connect.py

One command, one Bash call. It opens the browser on Google's consent screen, the person
clicks Allow, it saves `token.json`, then it prints the address it connected and the
message count. Print those lines as they are. Do not summarise them.

The permission it asks for is `gmail.modify`. Google's own wording for it is "Read,
compose, and send emails from your Gmail account". If the person asks why "send" is in
there: Google has no scope that allows drafts but not sending. What keeps this agent from
sending is that no tool in this folder can send. What the scope cannot do, for anyone, is
permanently delete mail.

## When it is red

Read the actual error, work out what is wrong on this machine, and say it in one or two
plain sentences. Then offer the one fix, and ask before doing anything.

- **credentials.json not found.** The four console steps. The file goes in this folder,
  with exactly that name.
- **"is a Web application client".** The wrong client type was created. Make a new one of
  type Desktop app and download that JSON.
- **The browser says "Access blocked" or "has not completed the Google verification
  process".** The consent screen is in Testing and this Google account is not on its
  test-user list. Add the account under Audience > Test users, or set the app to Internal
  on a Google Workspace account. A personal tool never needs Google's verification.
- **"invalid_grant", token expired or revoked.** Delete `token.json` and run the tool
  again. Apps left in Testing expire their tokens after seven days; Internal apps do not.
- **The browser never opened.** The tool prints the URL. Ask the person to open it
  themselves, on this machine, because the redirect comes back to localhost here.

## After it is green

Say: "Connected. Fetch for real with `uv run tools/fetch.py`, or run `/inbox`." Nothing else.

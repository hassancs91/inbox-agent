# /// script
# requires-python = ">=3.11"
# dependencies = ["google-auth>=2.30", "google-auth-oauthlib>=1.2", "google-api-python-client>=2.150"]
# ///
"""Fetch the new mail into work/inbox.json.

The first tool of the inbox agent. One job: get the emails, leave out the ones already
handled, and save the rest to a file. There is no AI in this file. Nothing here decides
what an email means.

    uv run tools/fetch.py              read your Gmail inbox (after /connect-gmail)
    uv run tools/fetch.py --sample     read fixtures/sample-inbox.json, no Gmail needed
    uv run tools/fetch.py --max 50     how many of the newest inbox messages to read (default 20)

Every email comes out in the same shape, whichever source it came from:
    id, threadId, date, from {name, email}, to, subject, body, labels

What comes out is the new mail, plus the corrections. memory/seen.json says which emails
the agent has handled and what label it put on each one:

    in memory, still carrying that label   handled, and left out
    in memory, carrying something else     you relabelled it by hand, so it comes back
    not in memory                          new, so it comes back

An email you relabelled comes back with two extra fields, so the brain does not have to
work out what changed:

    was   the category the agent gave it
    now   the category it carries now, or null when its AI/ label is gone

In --sample mode there is no Gmail, so the label a message carries is the one label.py
recorded in work/labels.json. Change a label there and the next run sees a correction,
exactly as it would in Gmail.
"""

import argparse
import base64
import html
import json
import re
from datetime import datetime, timezone
from email.utils import parseaddr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "sample-inbox.json"
OUT = ROOT / "work" / "inbox.json"
SEEN = ROOT / "memory" / "seen.json"
RECORDED = ROOT / "work" / "labels.json"
BODY_LIMIT = 4000  # characters; enough to understand an email, not enough to drown the brain
PREFIX = "AI/"  # the labels this agent puts on, and the only ones it reads back


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def fetch_sample() -> list[dict]:
    """The twelve emails that ship with this folder, wearing the labels of the last run."""
    emails = json.loads(FIXTURE.read_text(encoding="utf-8"))
    recorded = read_json(RECORDED)
    for email in emails:
        label = recorded.get(email["id"])
        if label and label not in email["labels"]:
            email["labels"] = [*email["labels"], label]
    return emails


def fetch_gmail(limit: int) -> list[dict]:
    """The newest messages in the INBOX, each fetched in full and reshaped."""
    from _gmail import service

    svc = service()
    # Messages carry label ids, not label names. One call turns AI/urgent back into a name.
    names = {l["id"]: l["name"] for l in svc.users().labels().list(userId="me").execute().get("labels", [])}
    listing = svc.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=limit).execute()
    emails = []
    for ref in listing.get("messages", []):
        msg = svc.users().messages().get(userId="me", id=ref["id"], format="full").execute()
        emails.append(shape(msg, names))
    return emails


def shape(msg: dict, names: dict) -> dict:
    """A Gmail API message -> the one shape every tool in this folder understands."""
    headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
    name, addr = parseaddr(headers.get("from", ""))
    stamp = int(msg.get("internalDate", 0)) / 1000
    return {
        "id": msg["id"],
        "threadId": msg["threadId"],
        "date": datetime.fromtimestamp(stamp, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        "from": {"name": name or addr, "email": addr},
        "to": headers.get("to", ""),
        "subject": headers.get("subject", "(no subject)"),
        "body": body_text(msg["payload"]) or msg.get("snippet", ""),
        "labels": [names.get(i, i) for i in msg.get("labelIds", [])],
    }


def sift(emails: list[dict]) -> tuple[list[dict], int, int]:
    """Leave out what is done, mark what I changed.

    Returns the emails this run has to work on, how many of them are new, and how many are
    corrections.
    """
    seen = read_json(SEEN)
    keep, fresh, changed = [], 0, 0
    for email in emails:
        record = seen.get(email["id"])
        if record is None:
            fresh += 1
            keep.append(email)
            continue
        mine = [l for l in email["labels"] if l.startswith(PREFIX)]
        if mine == [PREFIX + record["category"]]:
            continue  # handled, and the label it was given is still the label it has
        # Its label is not the one the agent put there, so a hand changed it. One AI label
        # names the category you chose; none, or several, names nothing you said.
        changed += 1
        email["was"] = record["category"]
        email["now"] = mine[0][len(PREFIX):] if len(mine) == 1 else None
        keep.append(email)
    return keep, fresh, changed


def body_text(payload: dict) -> str:
    """The plain-text body. Walks multipart messages; strips HTML only when there is no plain part."""
    plain: list[str] = []
    rich: list[str] = []

    def walk(part: dict) -> None:
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if mime == "text/plain" and data:
            plain.append(decode(data))
        elif mime == "text/html" and data:
            rich.append(decode(data))
        for sub in part.get("parts", []):
            walk(sub)

    walk(payload)
    text = "\n".join(plain) if plain else strip_html("\n".join(rich))
    return text.strip()[:BODY_LIMIT]


def decode(data: str) -> str:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")


def strip_html(markup: str) -> str:
    text = re.sub(r"<(script|style).*?</\1>", " ", markup, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</li>|</h[1-6]>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n\n", text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch the new mail into work/inbox.json.")
    parser.add_argument("--sample", action="store_true", help="read the sample inbox instead of Gmail")
    parser.add_argument("--max", type=int, default=20, help="newest inbox messages to read from Gmail (default 20)")
    args = parser.parse_args()

    emails = fetch_sample() if args.sample else fetch_gmail(args.max)
    keep, fresh, changed = sift(emails)

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(keep, indent=2, ensure_ascii=False), encoding="utf-8")
    tail = f"{len(keep)} written to {OUT.relative_to(ROOT).as_posix()}" if keep else "nothing to do"
    done = len(emails) - len(keep)
    print(f"{len(emails)} in the inbox: {fresh} new, {changed} you changed, {done} already done -> {tail}")


if __name__ == "__main__":
    main()
